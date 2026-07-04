"""Laboratory worklist, result, catalog, and patient-result routes."""

from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user
from sqlalchemy.orm import joinedload, selectinload

from auth.decorators import login_required, role_required
from extensions import db
from laboratory.forms import CancelLabOrderForm, LabOrderEditForm, LabTestForm, ResultForm
from models import Department, LabOrder, LabResult, LabTest, Patient, Role, User
from services.laboratory_service import (LaboratoryError, attach_lab_file, cancel_lab_order,
    collect_sample, create_lab_test, enter_lab_result, get_abnormal_results,
    get_pending_lab_orders, lab_attachment_path, review_lab_result, start_processing,
    update_lab_order, update_lab_result, update_lab_test, verify_lab_result)

laboratory_bp = Blueprint("laboratory", __name__, url_prefix="/laboratory")
patient_labs_bp = Blueprint("patient_labs", __name__, url_prefix="/patients")


def _order(order_id): return db.get_or_404(LabOrder, order_id)
def _test(test_id): return db.get_or_404(LabTest, test_id)
def _result(result_id): return db.get_or_404(LabResult, result_id)


def _can_view(order):
    if current_user.has_role("Super Admin", "Admin", "Laboratory"): return True
    if current_user.has_role("Doctor"): return bool(current_user.doctor_profile and order.doctor_id == current_user.doctor_profile.id)
    if current_user.has_role("Patient"):
        patient = db.session.scalar(db.select(Patient).where(Patient.user_id == current_user.id))
        return bool(patient and order.patient_id == patient.id and order.status in {"verified", "reviewed"})
    return False


def _scope(statement):
    if current_user.has_role("Super Admin", "Admin", "Laboratory"): return statement
    if current_user.has_role("Doctor") and current_user.doctor_profile: return statement.where(LabOrder.doctor_id == current_user.doctor_profile.id)
    abort(403)


def _order_choices(form):
    departments = db.session.scalars(db.select(Department).where(Department.is_active.is_(True), Department.deleted_at.is_(None)).order_by(Department.name)).all()
    lab_role = db.session.scalar(db.select(Role).where(Role.name == "Laboratory"))
    users = lab_role.users if lab_role else []
    form.department_id.choices = [("", "Unassigned")] + [(item.id, item.name) for item in departments]
    form.assigned_to_id.choices = [("", "Unassigned")] + [(item.id, item.full_name) for item in users if item.is_active and not item.is_deleted]


@laboratory_bp.get("")
@laboratory_bp.get("/")
@role_required("Laboratory", "Admin")
def dashboard():
    pending = get_pending_lab_orders(); abnormal = get_abnormal_results(); today = datetime.now(timezone.utc).date()
    results = db.session.scalars(db.select(LabResult).where(LabResult.deleted_at.is_(None))).all()
    all_orders = db.session.scalars(db.select(LabOrder).where(LabOrder.deleted_at.is_(None))).all()
    return render_template("laboratory/dashboard.html", pending=pending, abnormal=abnormal,
        collected_today=sum(bool(o.collected_at and o.collected_at.date() == today) for o in all_orders),
        awaiting_verification=sum(r.status == "entered" for r in results), critical=sum(r.is_critical for r in abnormal),
        completed_today=sum(bool(r.verified_at and r.verified_at.date() == today) for r in results))


@laboratory_bp.get("/orders")
@role_required("Laboratory", "Doctor", "Admin")
def orders():
    statement = _scope(db.select(LabOrder).options(joinedload(LabOrder.patient), joinedload(LabOrder.doctor), selectinload(LabOrder.results)).where(LabOrder.deleted_at.is_(None)))
    status = request.args.get("status", ""); search = request.args.get("search", "").strip()
    if status: statement = statement.where(LabOrder.status == status)
    if search:
        term = f"%{search}%"; statement = statement.join(LabOrder.patient).where(db.or_(LabOrder.order_number.ilike(term), LabOrder.test_name.ilike(term), Patient.medical_record_number.ilike(term), Patient.first_name.ilike(term), Patient.last_name.ilike(term)))
    pagination = db.paginate(statement.order_by(LabOrder.ordered_at.desc()), page=request.args.get("page", 1, type=int), per_page=20, error_out=False)
    return render_template("laboratory/orders.html", orders=pagination.items, pagination=pagination, status=status, search=search)


@laboratory_bp.route("/orders/<order_id>", methods=["GET", "POST"])
@role_required("Laboratory", "Doctor", "Admin", "Patient")
def order_detail(order_id):
    order = _order(order_id)
    if not _can_view(order): abort(403)
    form = LabOrderEditForm(obj=order); _order_choices(form)
    if form.validate_on_submit():
        if not current_user.has_role("Super Admin", "Admin", "Laboratory"): abort(403)
        try:
            update_lab_order(order, actor=current_user, priority=form.priority.data, department_id=form.department_id.data,
                assigned_to_id=form.assigned_to_id.data, clinical_notes=form.clinical_notes.data)
            flash("Laboratory order updated.", "success"); return redirect(url_for("laboratory.order_detail", order_id=order.id))
        except LaboratoryError as exc: flash(str(exc), "danger")
    return render_template("laboratory/order_detail.html", order=order, form=form, cancel_form=CancelLabOrderForm())


@laboratory_bp.post("/orders/<order_id>/cancel")
@role_required("Laboratory", "Admin")
def cancel(order_id):
    order = _order(order_id); form = CancelLabOrderForm()
    if not form.validate_on_submit(): abort(400)
    try: cancel_lab_order(order, actor=current_user, reason=form.reason.data); flash("Laboratory order cancelled.", "success")
    except LaboratoryError as exc: flash(str(exc), "danger")
    return redirect(url_for("laboratory.order_detail", order_id=order.id))


@laboratory_bp.post("/orders/<order_id>/collect-sample")
@role_required("Laboratory", "Admin")
def collect(order_id):
    order = _order(order_id)
    try: collect_sample(order, actor=current_user); flash("Sample collected.", "success")
    except LaboratoryError as exc: flash(str(exc), "danger")
    return redirect(url_for("laboratory.order_detail", order_id=order.id))


@laboratory_bp.post("/orders/<order_id>/start-processing")
@role_required("Laboratory", "Admin")
def process(order_id):
    order = _order(order_id)
    try: start_processing(order, actor=current_user); flash("Sample processing started.", "success")
    except LaboratoryError as exc: flash(str(exc), "danger")
    return redirect(url_for("laboratory.order_detail", order_id=order.id))


@laboratory_bp.route("/orders/<order_id>/enter-result", methods=["GET", "POST"])
@role_required("Laboratory")
def enter_result(order_id):
    order = _order(order_id); form = ResultForm()
    if form.validate_on_submit():
        try:
            result = enter_lab_result(order, actor=current_user, **{name: getattr(form, name).data for name in ("component_name", "result_type", "value_numeric", "value_text", "unit", "reference_range", "abnormal_flag", "comments")})
            if form.attachment.data: attach_lab_file(result, form.attachment.data, actor=current_user)
            flash("Laboratory result entered.", "success"); return redirect(url_for("laboratory.order_detail", order_id=order.id))
        except LaboratoryError as exc: flash(str(exc), "danger")
    return render_template("laboratory/enter_result.html", order=order, form=form)


@laboratory_bp.route("/orders/<order_id>/results/<result_id>/edit", methods=["GET", "POST"])
@role_required("Laboratory")
def edit_result(order_id, result_id):
    order = _order(order_id); result = _result(result_id)
    if result.lab_order_id != order.id: abort(400)
    form = ResultForm(obj=result)
    if form.validate_on_submit():
        try:
            update_lab_result(result, actor=current_user, **{name: getattr(form, name).data for name in ("component_name", "result_type", "value_numeric", "value_text", "unit", "reference_range", "abnormal_flag", "comments")})
            if form.attachment.data: attach_lab_file(result, form.attachment.data, actor=current_user)
            flash("Laboratory result updated.", "success"); return redirect(url_for("laboratory.order_detail", order_id=order.id))
        except LaboratoryError as exc: flash(str(exc), "danger")
    return render_template("laboratory/enter_result.html", order=order, result=result, form=form)


@laboratory_bp.get("/orders/<order_id>/results/<result_id>/attachment")
@login_required
def result_attachment(order_id, result_id):
    order = _order(order_id); result = _result(result_id)
    if result.lab_order_id != order.id or not _can_view(order): abort(403)
    try: path = lab_attachment_path(result)
    except FileNotFoundError: abort(404)
    return send_file(path, as_attachment=True, download_name=result.attachment_name, mimetype=result.attachment_mime_type)


@laboratory_bp.post("/orders/<order_id>/verify")
@login_required
def verify(order_id):
    if not (current_user.has_role("Super Admin", "Admin") or current_user.has_permission("laboratory.validate")): abort(403)
    order = _order(order_id); result = _result(request.form.get("result_id"))
    if result.lab_order_id != order.id: abort(400)
    try: verify_lab_result(result, actor=current_user); flash("Result verified.", "success")
    except LaboratoryError as exc: flash(str(exc), "danger")
    return redirect(url_for("laboratory.order_detail", order_id=order.id))


@laboratory_bp.post("/orders/<order_id>/review")
@role_required("Doctor")
def review(order_id):
    order = _order(order_id); result = _result(request.form.get("result_id"))
    if result.lab_order_id != order.id: abort(400)
    try: review_lab_result(result, actor=current_user); flash("Result reviewed.", "success")
    except (LaboratoryError, PermissionError) as exc: flash(str(exc), "danger")
    return redirect(url_for("laboratory.order_detail", order_id=order.id))


@laboratory_bp.get("/catalog")
@role_required("Laboratory", "Admin")
def catalog():
    tests = db.session.scalars(db.select(LabTest).where(LabTest.deleted_at.is_(None)).order_by(LabTest.category, LabTest.name)).all()
    return render_template("laboratory/catalog.html", tests=tests)


@laboratory_bp.route("/catalog/create", methods=["GET", "POST"])
@role_required("Admin")
def catalog_create():
    form = LabTestForm()
    if form.validate_on_submit():
        try:
            create_lab_test(actor=current_user, **{name: getattr(form, name).data for name in ("code", "name", "category", "unit", "reference_range", "sample_type", "turnaround_minutes", "is_active")})
            flash("Laboratory test created.", "success"); return redirect(url_for("laboratory.catalog"))
        except LaboratoryError as exc: flash(str(exc), "danger")
    return render_template("laboratory/catalog_form.html", form=form, test=None)


@laboratory_bp.route("/catalog/<test_id>/edit", methods=["GET", "POST"])
@role_required("Admin")
def catalog_edit(test_id):
    test = _test(test_id); form = LabTestForm(obj=test)
    if form.validate_on_submit():
        try:
            update_lab_test(test, actor=current_user, **{name: getattr(form, name).data for name in ("code", "name", "category", "unit", "reference_range", "sample_type", "turnaround_minutes", "is_active")})
            flash("Laboratory test updated.", "success"); return redirect(url_for("laboratory.catalog"))
        except LaboratoryError as exc: flash(str(exc), "danger")
    return render_template("laboratory/catalog_form.html", form=form, test=test)


@patient_labs_bp.get("/<patient_id>/lab-results")
@login_required
def patient_results(patient_id):
    patient = db.get_or_404(Patient, patient_id)
    if current_user.has_role("Patient") and patient.user_id != current_user.id: abort(403)
    if not current_user.has_role("Super Admin", "Admin", "Doctor", "Laboratory", "Patient"): abort(403)
    statement = db.select(LabResult).join(LabResult.order).where(LabOrder.patient_id == patient.id, LabResult.status.in_(["verified", "reviewed"])).order_by(LabResult.resulted_at.desc())
    if current_user.has_role("Doctor"):
        if not current_user.doctor_profile: abort(403)
        statement = statement.where(LabOrder.doctor_id == current_user.doctor_profile.id)
    results = db.session.scalars(statement).all()
    return render_template("patients/lab_results.html", patient=patient, results=results)
