"""Administrator-only user and role management routes."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.orm import joinedload, selectinload

from auth.decorators import role_required
from extensions import db
from models import Department, Doctor, Permission, Role, Specialty, User
from services.user_management_service import (activate_user, assign_permissions,
                                               create_user, deactivate_user,
                                               reset_user_password, search_users,
                                               update_user)
from users.forms import (CreateUserForm, EditUserForm, EmptyForm,
                         ResetPasswordForm, RolePermissionsForm)

users_bp = Blueprint("users_admin", __name__, url_prefix="/users")
roles_bp = Blueprint("roles_admin", __name__, url_prefix="/roles")


def _available_roles():
    statement = db.select(Role).where(Role.is_active.is_(True), Role.deleted_at.is_(None)).order_by(Role.name)
    roles = db.session.execute(statement).scalars().all()
    return roles if current_user.has_role("Super Admin") else [role for role in roles if role.name not in {"Super Admin", "Admin"}]


def _configure_user_form(form):
    form.role_id.choices = [(role.id, role.name) for role in _available_roles()]
    form.department_id.choices = [("", "No department")] + [(item.id, item.name) for item in db.session.execute(db.select(Department).where(Department.is_active.is_(True)).order_by(Department.name)).scalars()]
    form.specialty_id.choices = [("", "Not assigned / not a doctor")] + [(item.id, item.name) for item in db.session.execute(db.select(Specialty).where(Specialty.is_active.is_(True)).order_by(Specialty.name)).scalars()]


def _user_or_404(user_id):
    statement = db.select(User).options(selectinload(User.roles), joinedload(User.department), joinedload(User.doctor_profile).joinedload(Doctor.specialty)).where(User.id == user_id, User.deleted_at.is_(None))
    return db.first_or_404(statement)


def _guard_target(user):
    if not current_user.has_role("Super Admin") and user.has_role("Super Admin", "Admin"):
        abort(403)


@users_bp.get("")
@users_bp.get("/")
@role_required("Super Admin", "Admin")
def index():
    filters = {key: request.args.get(key, "").strip() for key in ("search", "role_id", "status", "department_id")}
    pagination = search_users(**filters, page=request.args.get("page", 1, type=int))
    roles = db.session.execute(db.select(Role).order_by(Role.name)).scalars().all()
    departments = db.session.execute(db.select(Department).order_by(Department.name)).scalars().all()
    return render_template("users/index.html", pagination=pagination, users=pagination.items, roles=roles, departments=departments, filters=filters)


@users_bp.route("/create", methods=["GET", "POST"])
@role_required("Super Admin", "Admin")
def create():
    form = CreateUserForm()
    _configure_user_form(form)
    if form.validate_on_submit():
        role = db.session.get(Role, form.role_id.data)
        if role not in _available_roles():
            abort(403)
        try:
            user = create_user(username=form.username.data, email=form.email.data, first_name=form.first_name.data, last_name=form.last_name.data, phone=form.phone.data, password=form.password.data, role=role, department_id=form.department_id.data, specialty_id=form.specialty_id.data, license_number=form.license_number.data, actor=current_user)
            flash(f"User {user.username} was created.", "success")
            return redirect(url_for("users_admin.detail", user_id=user.id))
        except (ValueError, PermissionError) as exc:
            flash(str(exc), "danger")
    return render_template("users/create.html", form=form)


@users_bp.get("/<user_id>")
@role_required("Super Admin", "Admin")
def detail(user_id):
    user = _user_or_404(user_id)
    return render_template("users/detail.html", user=user, action_form=EmptyForm())


@users_bp.route("/<user_id>/edit", methods=["GET", "POST"])
@role_required("Super Admin", "Admin")
def edit(user_id):
    user = _user_or_404(user_id)
    _guard_target(user)
    if user.id == current_user.id:
        abort(403)
    form = EditUserForm(obj=user)
    _configure_user_form(form)
    if request.method == "GET":
        form.role_id.data = user.role_id
        form.department_id.data = user.department_id or ""
        form.specialty_id.data = user.doctor_profile.specialty_id if user.doctor_profile and user.doctor_profile.specialty_id else ""
        form.license_number.data = user.doctor_profile.license_number if user.doctor_profile else ""
    if form.validate_on_submit():
        role = db.session.get(Role, form.role_id.data)
        if role not in _available_roles():
            abort(403)
        try:
            update_user(user, username=form.username.data, email=form.email.data, first_name=form.first_name.data, last_name=form.last_name.data, phone=form.phone.data, role=role, department_id=form.department_id.data, specialty_id=form.specialty_id.data, license_number=form.license_number.data, actor=current_user)
            flash("User details were updated.", "success")
            return redirect(url_for("users_admin.detail", user_id=user.id))
        except (ValueError, PermissionError) as exc:
            flash(str(exc), "danger")
    return render_template("users/edit.html", form=form, user=user)


@users_bp.post("/<user_id>/activate")
@role_required("Super Admin", "Admin")
def activate(user_id):
    user, form = _user_or_404(user_id), EmptyForm()
    _guard_target(user)
    if not form.validate_on_submit(): abort(400)
    try:
        activate_user(user, current_user)
        flash("User account activated.", "success")
    except PermissionError as exc: flash(str(exc), "danger")
    return redirect(url_for("users_admin.detail", user_id=user.id))


@users_bp.post("/<user_id>/deactivate")
@role_required("Super Admin", "Admin")
def deactivate(user_id):
    user, form = _user_or_404(user_id), EmptyForm()
    _guard_target(user)
    if not form.validate_on_submit(): abort(400)
    try:
        deactivate_user(user, current_user)
        flash("User account deactivated.", "success")
    except PermissionError as exc: flash(str(exc), "danger")
    return redirect(url_for("users_admin.detail", user_id=user.id))


@users_bp.route("/<user_id>/reset-password", methods=["GET", "POST"])
@role_required("Super Admin", "Admin")
def reset_password(user_id):
    user = _user_or_404(user_id)
    _guard_target(user)
    if user.id == current_user.id: abort(403)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            reset_user_password(user, form.password.data, current_user)
            flash("Temporary password set. The user must change it after login.", "success")
            return redirect(url_for("users_admin.detail", user_id=user.id))
        except (ValueError, PermissionError) as exc: flash(str(exc), "danger")
    return render_template("users/reset_password.html", form=form, user=user)


@roles_bp.get("")
@roles_bp.get("/")
@role_required("Super Admin", "Admin")
def index():
    roles = db.session.execute(db.select(Role).options(selectinload(Role.permissions), selectinload(Role.users)).order_by(Role.name)).scalars().all()
    return render_template("roles/index.html", roles=roles)


@roles_bp.route("/<role_id>/permissions", methods=["GET", "POST"])
@role_required("Super Admin", "Admin")
def permissions(role_id):
    role = db.get_or_404(Role, role_id)
    form = RolePermissionsForm()
    all_permissions = db.session.execute(db.select(Permission).order_by(Permission.module, Permission.code)).scalars().all()
    form.permission_ids.choices = [(item.id, item.code) for item in all_permissions]
    if request.method == "GET": form.permission_ids.data = [item.id for item in role.permissions]
    if form.validate_on_submit():
        if not current_user.has_role("Super Admin"): abort(403)
        try:
            assign_permissions(role, form.permission_ids.data, current_user)
            flash("Role permissions updated.", "success")
            return redirect(url_for("roles_admin.permissions", role_id=role.id))
        except PermissionError as exc: flash(str(exc), "danger")
    grouped = {}
    for item in all_permissions: grouped.setdefault(item.module, []).append(item)
    return render_template("roles/permissions.html", role=role, form=form, grouped_permissions=grouped)
