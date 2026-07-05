"""Administration dashboards and operational management routes."""

from datetime import datetime
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload, selectinload

from administration.forms import DepartmentForm, EmptyForm, StaffAssignmentForm
from extensions import db
from models import Department, Doctor, Role, Specialty, User
from services.administration_service import (
    AdministrationServiceError, assign_staff_to_department, create_department,
    deactivate_department, get_administration_dashboard, get_operational_kpis,
    get_resource_allocation, get_staff_activity, log_administration_access,
    update_department,
)

administration_bp = Blueprint("administration", __name__, url_prefix="/administration")


def administration_view_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.has_role("Super Admin", "Admin") or current_user.has_permission("administration.view"):
            return view(*args, **kwargs)
        abort(403)
    return wrapped


def administration_manage_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.has_role("Super Admin", "Admin"):
            return view(*args, **kwargs)
        abort(403)
    return wrapped


def _scope_department():
    return None if current_user.has_role("Super Admin", "Admin") else current_user.department_id


def _date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date() if value else None
    except ValueError:
        return None


def _department_or_404(department_id):
    return db.get_or_404(Department, department_id)


@administration_bp.get("")
@administration_bp.get("/")
@administration_view_required
def dashboard():
    return render_template("administration/dashboard.html", dashboard=get_administration_dashboard(_scope_department()))


@administration_bp.get("/staff")
@administration_view_required
def staff():
    filters = {key: request.args.get(key, "").strip() for key in ("role_id", "department_id", "specialty_id", "status")}
    statement = db.select(User).options(selectinload(User.roles), joinedload(User.department),
        joinedload(User.doctor_profile).joinedload(Doctor.specialty)).where(User.deleted_at.is_(None))
    scoped = _scope_department()
    department_id = scoped or filters["department_id"]
    if department_id: statement = statement.where(User.department_id == department_id)
    if filters["role_id"]: statement = statement.where(User.roles.any(Role.id == filters["role_id"]))
    if filters["specialty_id"]: statement = statement.where(User.doctor_profile.has(Doctor.specialty_id == filters["specialty_id"]))
    if filters["status"] in {"active", "inactive"}: statement = statement.where(User.is_active.is_(filters["status"] == "active"))
    users = db.session.scalars(statement.order_by(User.last_name, User.first_name)).unique().all()
    return render_template("administration/staff.html", users=users, activity=get_staff_activity(department_id), filters=filters,
        roles=db.session.scalars(db.select(Role).order_by(Role.name)).all(),
        departments=db.session.scalars(db.select(Department).order_by(Department.name)).all(),
        specialties=db.session.scalars(db.select(Specialty).order_by(Specialty.name)).all())


@administration_bp.get("/departments")
@administration_view_required
def departments():
    statement = db.select(Department).where(Department.deleted_at.is_(None)).order_by(Department.name)
    if _scope_department(): statement = statement.where(Department.id == _scope_department())
    return render_template("administration/departments.html", departments=db.session.scalars(statement).all(), action_form=EmptyForm())


@administration_bp.route("/departments/create", methods=["GET", "POST"])
@administration_manage_required
def department_create():
    form = DepartmentForm()
    if form.validate_on_submit():
        try:
            create_department(code=form.code.data, name=form.name.data, department_type=form.department_type.data,
                description=form.description.data, location=form.location.data, actor=current_user)
            flash("Department created.", "success")
            return redirect(url_for("administration.departments"))
        except AdministrationServiceError as exc: flash(str(exc), "danger")
    return render_template("administration/department_form.html", form=form, title="Create department")


@administration_bp.route("/departments/<department_id>/edit", methods=["GET", "POST"])
@administration_manage_required
def department_edit(department_id):
    department = _department_or_404(department_id)
    form = DepartmentForm(obj=department)
    if form.validate_on_submit():
        try:
            update_department(department, actor=current_user, code=form.code.data, name=form.name.data,
                department_type=form.department_type.data, description=form.description.data, location=form.location.data)
            flash("Department updated.", "success")
            return redirect(url_for("administration.departments"))
        except AdministrationServiceError as exc: flash(str(exc), "danger")
    return render_template("administration/department_form.html", form=form, title="Edit department", department=department)


@administration_bp.post("/departments/<department_id>/deactivate")
@administration_manage_required
def department_deactivate(department_id):
    if not EmptyForm().validate_on_submit(): abort(400)
    deactivate_department(_department_or_404(department_id), current_user)
    flash("Department deactivated.", "success")
    return redirect(url_for("administration.departments"))


@administration_bp.post("/departments/<department_id>/activate")
@administration_manage_required
def department_activate(department_id):
    if not EmptyForm().validate_on_submit(): abort(400)
    update_department(_department_or_404(department_id), actor=current_user, is_active=True)
    flash("Department activated.", "success")
    return redirect(url_for("administration.departments"))


@administration_bp.route("/resources", methods=["GET", "POST"])
@administration_view_required
def resources():
    form = StaffAssignmentForm()
    departments = db.session.scalars(db.select(Department).where(Department.is_active.is_(True)).order_by(Department.name)).all()
    users = db.session.scalars(db.select(User).where(User.deleted_at.is_(None)).order_by(User.last_name, User.first_name)).all()
    specialties = db.session.scalars(db.select(Specialty).where(Specialty.is_active.is_(True)).order_by(Specialty.name)).all()
    form.user_id.choices = [(x.id, x.full_name) for x in users]
    form.department_id.choices = [(x.id, x.name) for x in departments]
    form.specialty_id.choices = [("", "Keep current / not applicable")] + [(x.id, x.name) for x in specialties]
    if form.validate_on_submit():
        if not current_user.has_role("Super Admin", "Admin"): abort(403)
        user, department = db.session.get(User, form.user_id.data), db.session.get(Department, form.department_id.data)
        if not user or not department: abort(404)
        specialty = db.session.get(Specialty, form.specialty_id.data) if form.specialty_id.data else None
        assign_staff_to_department(user, department, current_user, specialty)
        flash("Staff assignment updated.", "success")
        return redirect(url_for("administration.resources"))
    return render_template("administration/resources.html", allocations=get_resource_allocation(_scope_department()), form=form)


@administration_bp.get("/kpis")
@administration_view_required
def kpis():
    department_id = _scope_department() or request.args.get("department_id") or None
    data = get_operational_kpis(_date(request.args.get("start_date")), _date(request.args.get("end_date")),
                                department_id, request.args.get("doctor_id") or None)
    log_administration_access("administration.kpi_accessed", current_user, {"department_id": department_id})
    return render_template("administration/kpis.html", kpis=data, departments=db.session.scalars(db.select(Department).order_by(Department.name)).all(),
        doctors=db.session.scalars(db.select(Doctor).options(joinedload(Doctor.user)).order_by(Doctor.title)).all(), filters=request.args)


@administration_bp.get("/reports")
@administration_view_required
def reports():
    department_id = _scope_department() or request.args.get("department_id") or None
    data = get_operational_kpis(_date(request.args.get("start_date")), _date(request.args.get("end_date")),
                                department_id, request.args.get("doctor_id") or None)
    log_administration_access("administration.report_accessed", current_user, {"department_id": department_id})
    return render_template("administration/reports.html", report=data, departments=db.session.scalars(db.select(Department).order_by(Department.name)).all(),
        doctors=db.session.scalars(db.select(Doctor).options(joinedload(Doctor.user))).all(), filters=request.args)
