"""Radiology order, workflow, report, catalog, and patient-report routes."""

from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user
from sqlalchemy.orm import joinedload, selectinload

from auth.decorators import login_required, role_required
from extensions import db
from models import (
    Doctor,
    ImagingStudy,
    Patient,
    RadiologyAttachment,
    RadiologyOrder,
    RadiologyReport,
    Role,
)
from radiology.forms import (
    CancelRadiologyOrderForm,
    ImagingStudyForm,
    RadiologyOrderForm,
    ReportForm,
    ScheduleStudyForm,
    VerifyReportForm,
)
from services.radiology_service import (
    RadiologyError,
    cancel_radiology_order,
    create_imaging_study,
    create_radiology_report,
    get_pending_radiology_orders,
    get_reports_waiting_verification,
    get_today_schedule,
    mark_imaging_performed,
    mark_patient_arrived,
    radiology_attachment_path,
    review_radiology_report,
    schedule_radiology_order,
    update_imaging_study,
    update_radiology_order,
    verify_radiology_report,
)


radiology_bp = Blueprint("radiology", __name__, url_prefix="/radiology")
patient_radiology_bp = Blueprint("patient_radiology", __name__, url_prefix="/patients")


def _order(order_id):
    return db.get_or_404(RadiologyOrder, order_id)


def _report(report_id):
    return db.get_or_404(RadiologyReport, report_id)


def _study(study_id):
    return db.get_or_404(ImagingStudy, study_id)


def _attachment(attachment_id):
    return db.get_or_404(RadiologyAttachment, attachment_id)


def _patient_profile():
    return db.session.scalar(
        db.select(Patient).where(
            Patient.user_id == current_user.id,
            Patient.deleted_at.is_(None),
        )
    )


def _can_view(order):
    if current_user.has_role("Super Admin", "Admin", "Radiology"):
        return True

    if current_user.has_role("Doctor"):
        return bool(current_user.doctor_profile and order.doctor_id == current_user.doctor_profile.id)

    if current_user.has_role("Patient"):
        patient = _patient_profile()
        return bool(
            patient
            and order.patient_id == patient.id
            and any(report.status in {"verified", "reviewed"} for report in order.reports)
        )

    return False


def _scope(statement):
    if current_user.has_role("Super Admin", "Admin", "Radiology"):
        return statement

    if current_user.has_role("Doctor") and current_user.doctor_profile:
        return statement.where(RadiologyOrder.doctor_id == current_user.doctor_profile.id)

    abort(403)


def _radiology_user_choices():
    role = db.session.scalar(db.select(Role).where(Role.name == "Radiology"))
    users = role.users if role else []
    return [("", "Unassigned")] + [
        (user.id, user.full_name)
        for user in users
        if user.is_active and not user.is_deleted
    ]


def _order_choices(form):
    patients = db.session.scalars(
        db.select(Patient)
        .where(Patient.deleted_at.is_(None), Patient.is_active.is_(True))
        .order_by(Patient.first_name, Patient.last_name)
    ).all()

    doctors = db.session.scalars(
        db.select(Doctor)
        .options(joinedload(Doctor.user))
        .where(Doctor.deleted_at.is_(None), Doctor.is_active.is_(True))
        .order_by(Doctor.id)
    ).unique().all()

    studies = db.session.scalars(
        db.select(ImagingStudy)
        .where(ImagingStudy.deleted_at.is_(None), ImagingStudy.is_active.is_(True))
        .order_by(ImagingStudy.modality, ImagingStudy.name)
    ).all()

    form.patient_id.choices = [
        (patient.id, f"{patient.first_name} {patient.last_name} · {patient.medical_record_number}")
        for patient in patients
    ]

    form.doctor_id.choices = [
        (doctor.id, doctor.user.full_name if doctor.user else doctor.id)
        for doctor in doctors
    ]

    form.imaging_study_id.choices = [("", "Manual study")] + [
        (study.id, f"{study.modality} · {study.name} · {study.body_region}")
        for study in studies
    ]


def _schedule_choices(form):
    form.assigned_radiology_user_id.choices = _radiology_user_choices()


@radiology_bp.get("")
@radiology_bp.get("/")
@role_required("Radiology", "Admin")
def dashboard():
    pending = get_pending_radiology_orders()
    today_schedule = get_today_schedule()
    awaiting_verification = get_reports_waiting_verification()
    today = datetime.now(timezone.utc).date()

    all_orders = db.session.scalars(
        db.select(RadiologyOrder).where(RadiologyOrder.deleted_at.is_(None))
    ).all()

    all_reports = db.session.scalars(
        db.select(RadiologyReport).where(RadiologyReport.deleted_at.is_(None))
    ).all()

    return render_template(
        "radiology/dashboard.html",
        pending=pending,
        today_schedule=today_schedule,
        scheduled_today=len(today_schedule),
        performed_today=sum(bool(o.imaging_performed_at and o.imaging_performed_at.date() == today) for o in all_orders),
        awaiting_verification=awaiting_verification,
        urgent_findings=sum(bool(o.urgent_finding_flag) for o in all_orders),
        completed_today=sum(bool(r.verified_at and r.verified_at.date() == today) for r in all_reports),
    )


@radiology_bp.get("/orders")
@role_required("Radiology", "Doctor", "Admin")
def orders():
    statement = _scope(
        db.select(RadiologyOrder)
        .options(
            joinedload(RadiologyOrder.patient),
            joinedload(RadiologyOrder.doctor).joinedload(Doctor.user),
            selectinload(RadiologyOrder.reports),
        )
        .where(RadiologyOrder.deleted_at.is_(None))
    )

    status = request.args.get("status", "")
    modality = request.args.get("modality", "")
    search = request.args.get("search", "").strip()

    if status:
        statement = statement.where(RadiologyOrder.status == status)

    if modality:
        statement = statement.where(RadiologyOrder.modality == modality)

    if search:
        term = f"%{search}%"
        statement = statement.join(RadiologyOrder.patient).where(
            db.or_(
                RadiologyOrder.order_number.ilike(term),
                RadiologyOrder.modality.ilike(term),
                RadiologyOrder.body_part.ilike(term),
                Patient.medical_record_number.ilike(term),
                Patient.first_name.ilike(term),
                Patient.last_name.ilike(term),
            )
        )

    pagination = db.paginate(
        statement.order_by(RadiologyOrder.ordered_at.desc()),
        page=request.args.get("page", 1, type=int),
        per_page=20,
        error_out=False,
    )

    return render_template(
        "radiology/orders.html",
        orders=pagination.items,
        pagination=pagination,
        status=status,
        modality=modality,
        search=search,
    )


@radiology_bp.route("/orders/create", methods=["GET", "POST"])
@role_required("Doctor", "Admin")
def create_order():
    form = RadiologyOrderForm()
    _order_choices(form)

    if form.validate_on_submit():
        try:
            study = db.session.get(ImagingStudy, form.imaging_study_id.data) if form.imaging_study_id.data else None
            count = db.session.scalar(db.select(db.func.count(RadiologyOrder.id))) or 0
            order = RadiologyOrder(
                order_number=f"RAD-{datetime.now(timezone.utc):%Y%m%d}-{count + 1:04d}",
                patient_id=form.patient_id.data,
                doctor_id=form.doctor_id.data,
                imaging_study_id=study.id if study else None,
                modality=study.modality if study else form.modality.data,
                body_part=study.body_region if study else form.body_part.data,
                priority=form.priority.data,
                status="requested",
                ordered_at=datetime.now(timezone.utc),
                clinical_indication=form.clinical_indication.data,
            )
            db.session.add(order)
            db.session.commit()
            flash("Radiology order created.", "success")
            return redirect(url_for("radiology.order_detail", order_id=order.id))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    return render_template("radiology/order_form.html", form=form)


@radiology_bp.route("/orders/<order_id>", methods=["GET", "POST"])
@role_required("Radiology", "Doctor", "Admin", "Patient")
def order_detail(order_id):
    order = _order(order_id)

    if not _can_view(order):
        abort(403)

    schedule_form = ScheduleStudyForm()
    _schedule_choices(schedule_form)

    cancel_form = CancelRadiologyOrderForm()
    action_form = VerifyReportForm()

    return render_template(
        "radiology/order_detail.html",
        order=order,
        schedule_form=schedule_form,
        cancel_form=cancel_form,
        action_form=action_form,
    )


@radiology_bp.route("/orders/<order_id>/schedule", methods=["GET", "POST"])
@role_required("Radiology", "Admin")
def schedule(order_id):
    order = _order(order_id)
    form = ScheduleStudyForm()
    _schedule_choices(form)

    if form.validate_on_submit():
        try:
            schedule_radiology_order(
                order,
                actor=current_user,
                scheduled_at=form.scheduled_at.data,
                assigned_radiology_user_id=form.assigned_radiology_user_id.data or None,
            )
            flash("Radiology study scheduled.", "success")
            return redirect(url_for("radiology.order_detail", order_id=order.id))
        except RadiologyError as exc:
            flash(str(exc), "danger")

    return render_template("radiology/order_detail.html", order=order, schedule_form=form, cancel_form=CancelRadiologyOrderForm(), action_form=VerifyReportForm())


@radiology_bp.post("/orders/<order_id>/arrived")
@role_required("Radiology", "Admin")
def arrived(order_id):
    order = _order(order_id)

    try:
        mark_patient_arrived(order, actor=current_user)
        flash("Patient marked as arrived.", "success")
    except RadiologyError as exc:
        flash(str(exc), "danger")

    return redirect(url_for("radiology.order_detail", order_id=order.id))


@radiology_bp.post("/orders/<order_id>/perform")
@role_required("Radiology", "Admin")
def perform(order_id):
    order = _order(order_id)

    try:
        mark_imaging_performed(order, actor=current_user)
        flash("Imaging marked as performed.", "success")
    except RadiologyError as exc:
        flash(str(exc), "danger")

    return redirect(url_for("radiology.order_detail", order_id=order.id))


@radiology_bp.route("/orders/<order_id>/report", methods=["GET", "POST"])
@role_required("Radiology")
def report(order_id):
    order = _order(order_id)
    existing = order.reports[0] if order.reports else None
    form = ReportForm(obj=existing)

    if request.method == "GET" and existing:
        form.clinical_indication.data = existing.clinical_indication
        form.technique.data = existing.technique
        form.findings.data = existing.findings
        form.impression.data = existing.impression
        form.recommendations.data = existing.recommendations
        form.is_abnormal.data = existing.is_abnormal
        form.is_critical.data = existing.is_critical

    if form.validate_on_submit():
        try:
            create_radiology_report(
                order,
                actor=current_user,
                radiologist_id=current_user.doctor_profile.id if current_user.doctor_profile else None,
                clinical_indication=form.clinical_indication.data,
                technique=form.technique.data,
                findings=form.findings.data,
                impression=form.impression.data,
                recommendations=form.recommendations.data,
                is_abnormal=form.is_abnormal.data,
                is_critical=form.is_critical.data,
            )
            flash("Radiology report saved.", "success")
            return redirect(url_for("radiology.order_detail", order_id=order.id))
        except RadiologyError as exc:
            flash(str(exc), "danger")

    return render_template("radiology/report_form.html", order=order, form=form)


@radiology_bp.post("/orders/<order_id>/verify")
@login_required
def verify(order_id):
    if not (current_user.has_role("Super Admin", "Admin", "Radiology") or current_user.has_permission("radiology.verify")):
        abort(403)

    order = _order(order_id)
    report = _report(request.form.get("report_id"))

    if report.radiology_order_id != order.id:
        abort(400)

    try:
        verify_radiology_report(report, actor=current_user)
        flash("Radiology report verified.", "success")
    except RadiologyError as exc:
        flash(str(exc), "danger")

    return redirect(url_for("radiology.order_detail", order_id=order.id))


@radiology_bp.post("/orders/<order_id>/review")
@role_required("Doctor")
def review(order_id):
    order = _order(order_id)
    report = _report(request.form.get("report_id"))

    if report.radiology_order_id != order.id:
        abort(400)

    try:
        review_radiology_report(report, actor=current_user)
        flash("Radiology report reviewed.", "success")
    except (RadiologyError, PermissionError) as exc:
        flash(str(exc), "danger")

    return redirect(url_for("radiology.order_detail", order_id=order.id))


@radiology_bp.post("/orders/<order_id>/cancel")
@role_required("Radiology", "Admin")
def cancel(order_id):
    order = _order(order_id)
    form = CancelRadiologyOrderForm()

    if not form.validate_on_submit():
        abort(400)

    try:
        cancel_radiology_order(order, actor=current_user, reason=form.reason.data)
        flash("Radiology order cancelled.", "success")
    except RadiologyError as exc:
        flash(str(exc), "danger")

    return redirect(url_for("radiology.order_detail", order_id=order.id))


@radiology_bp.get("/orders/<order_id>/attachments/<attachment_id>")
@login_required
def attachment(order_id, attachment_id):
    order = _order(order_id)
    attachment = _attachment(attachment_id)

    if attachment.radiology_order_id != order.id or not _can_view(order):
        abort(403)

    try:
        path = radiology_attachment_path(attachment)
    except FileNotFoundError:
        abort(404)

    return send_file(
        path,
        as_attachment=True,
        download_name=attachment.original_name,
        mimetype=attachment.mime_type,
    )


@radiology_bp.get("/catalog")
@role_required("Radiology", "Admin")
def catalog():
    studies = db.session.scalars(
        db.select(ImagingStudy)
        .where(ImagingStudy.deleted_at.is_(None))
        .order_by(ImagingStudy.modality, ImagingStudy.name)
    ).all()

    return render_template("radiology/catalog.html", studies=studies)


@radiology_bp.route("/catalog/create", methods=["GET", "POST"])
@role_required("Admin")
def catalog_create():
    form = ImagingStudyForm()

    if form.validate_on_submit():
        try:
            create_imaging_study(
                actor=current_user,
                name=form.name.data,
                modality=form.modality.data,
                body_region=form.body_region.data,
                preparation_instructions=form.preparation_instructions.data,
                description=form.description.data,
                is_active=form.is_active.data,
            )
            flash("Imaging study created.", "success")
            return redirect(url_for("radiology.catalog"))
        except RadiologyError as exc:
            flash(str(exc), "danger")

    return render_template("radiology/catalog_form.html", form=form, study=None)


@radiology_bp.route("/catalog/<study_id>/edit", methods=["GET", "POST"])
@role_required("Admin")
def catalog_edit(study_id):
    study = _study(study_id)
    form = ImagingStudyForm(obj=study)

    if form.validate_on_submit():
        try:
            update_imaging_study(
                study,
                actor=current_user,
                name=form.name.data,
                modality=form.modality.data,
                body_region=form.body_region.data,
                preparation_instructions=form.preparation_instructions.data,
                description=form.description.data,
                is_active=form.is_active.data,
            )
            flash("Imaging study updated.", "success")
            return redirect(url_for("radiology.catalog"))
        except RadiologyError as exc:
            flash(str(exc), "danger")

    return render_template("radiology/catalog_form.html", form=form, study=study)


@patient_radiology_bp.get("/<patient_id>/radiology-reports")
@login_required
def patient_reports(patient_id):
    patient = db.get_or_404(Patient, patient_id)

    if current_user.has_role("Patient") and patient.user_id != current_user.id:
        abort(403)

    if not current_user.has_role("Super Admin", "Admin", "Doctor", "Radiology", "Patient"):
        abort(403)

    statement = (
        db.select(RadiologyReport)
        .join(RadiologyReport.order)
        .where(
            RadiologyOrder.patient_id == patient.id,
            RadiologyReport.status.in_(["verified", "reviewed"]),
        )
        .order_by(RadiologyReport.reported_at.desc())
    )

    if current_user.has_role("Doctor"):
        if not current_user.doctor_profile:
            abort(403)
        statement = statement.where(RadiologyOrder.doctor_id == current_user.doctor_profile.id)

    reports = db.session.scalars(statement).all()

    return render_template("patients/radiology_reports.html", patient=patient, reports=reports)