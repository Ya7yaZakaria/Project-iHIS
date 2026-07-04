"""Appointment booking and clinic workflow routes."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from appointments.forms import (
    AppointmentForm, AppointmentSearchForm, CancelAppointmentForm,
    CompleteAppointmentForm, FollowUpForm, NoShowForm, RescheduleForm,
    StartConsultationForm,
)
from auth.decorators import role_required
from extensions import db
from models import Appointment, Department, Doctor, Patient
from services import appointment_service

appointments_bp = Blueprint("appointments", __name__, url_prefix="/appointments")
MANAGERS = ("Receptionist", "Admin", "Super Admin")


def _get_appointment(appointment_id):
    return db.get_or_404(Appointment, appointment_id)


def _patient_profile():
    return db.session.execute(db.select(Patient).where(
        Patient.user_id == current_user.id, Patient.deleted_at.is_(None)
    )).scalar_one_or_none()


def _can_view(appointment):
    if current_user.has_role(*MANAGERS): return True
    if current_user.has_role("Doctor"):
        return bool(current_user.doctor_profile and appointment.doctor_id == current_user.doctor_profile.id)
    if current_user.has_role("Patient"):
        patient = _patient_profile()
        return bool(patient and appointment.patient_id == patient.id)
    return False


def _require_view(appointment):
    if not _can_view(appointment): abort(403)


def _require_assigned_doctor(appointment):
    doctor = current_user.doctor_profile
    if not current_user.has_role("Doctor") or not doctor or appointment.doctor_id != doctor.id: abort(403)
    return doctor


def _form_choices(form):
    patients = db.session.execute(db.select(Patient).where(
        Patient.deleted_at.is_(None), Patient.is_active.is_(True)
    ).order_by(Patient.last_name, Patient.first_name)).scalars().all()
    doctors = db.session.execute(db.select(Doctor).options(joinedload(Doctor.user), joinedload(Doctor.specialty)).where(
        Doctor.deleted_at.is_(None), Doctor.is_active.is_(True)
    )).scalars().unique().all()
    departments = db.session.execute(db.select(Department).where(
        Department.deleted_at.is_(None), Department.is_active.is_(True)
    ).order_by(Department.name)).scalars().all()
    if hasattr(form, "patient_id"):
        form.patient_id.choices = [(p.id, f"{p.medical_record_number} — {p.first_name} {p.last_name}") for p in patients]
    if hasattr(form, "doctor_id"):
        form.doctor_id.choices = [("", "Unassigned")] + [(d.id, f"{d.title + ' ' if d.title else ''}{d.user.full_name}") for d in doctors]
    if hasattr(form, "department_id"):
        form.department_id.choices = [("", "Select department")] + [(d.id, d.name) for d in departments]


def _search_form():
    form = AppointmentSearchForm(request.args, meta={"csrf": False})
    form.status.choices = [("", "All statuses")] + list(AppointmentForm.status.kwargs["choices"])
    _form_choices(form)
    form.doctor_id.choices[0] = ("", "All doctors")
    form.department_id.choices[0] = ("", "All departments")
    return form


def _scoped(statement):
    if current_user.has_role(*MANAGERS): return statement
    if current_user.has_role("Doctor") and current_user.doctor_profile:
        return statement.where(Appointment.doctor_id == current_user.doctor_profile.id)
    if current_user.has_role("Patient"):
        patient = _patient_profile()
        if patient: return statement.where(Appointment.patient_id == patient.id)
    abort(403)


@appointments_bp.get("")
@appointments_bp.get("/")
@role_required("Receptionist", "Doctor", "Admin", "Patient")
def index():
    form = _search_form()
    statement = _scoped(db.select(Appointment).options(
        joinedload(Appointment.patient), joinedload(Appointment.doctor).joinedload(Doctor.user),
        joinedload(Appointment.department)
    ).join(Appointment.patient).where(Appointment.deleted_at.is_(None)))
    search = (form.search.data or "").strip()
    if search:
        term = f"%{search}%"
        statement = statement.where(or_(Appointment.appointment_number.ilike(term), Appointment.reason.ilike(term),
            Patient.medical_record_number.ilike(term), Patient.first_name.ilike(term), Patient.last_name.ilike(term)))
    if form.date.data:
        start, end = appointment_service.day_bounds(form.date.data)
        statement = statement.where(Appointment.scheduled_start >= start, Appointment.scheduled_start < end)
    if form.doctor_id.data: statement = statement.where(Appointment.doctor_id == form.doctor_id.data)
    if form.department_id.data: statement = statement.where(Appointment.department_id == form.department_id.data)
    if form.status.data: statement = statement.where(Appointment.status == form.status.data)
    pagination = db.paginate(statement.order_by(Appointment.scheduled_start.desc()), page=request.args.get("page", 1, type=int), per_page=20, error_out=False)
    return render_template("appointments/index.html", appointments=pagination.items, pagination=pagination, form=form)


@appointments_bp.route("/create", methods=["GET", "POST"])
@role_required("Receptionist", "Admin")
def create():
    form = AppointmentForm(); _form_choices(form)
    form.status.choices = [("booked", "Booked"), ("confirmed", "Confirmed")]
    requested_patient = request.args.get("patient_id")
    if request.method == "GET" and requested_patient: form.patient_id.data = requested_patient
    if form.validate_on_submit():
        try:
            appointment = appointment_service.create_appointment(patient_id=form.patient_id.data, doctor_id=form.doctor_id.data or None,
                department_id=form.department_id.data or None, scheduled_start=form.scheduled_start.data, scheduled_end=form.scheduled_end.data,
                appointment_type=form.appointment_type.data, reason=form.reason.data or None, notes=form.notes.data or None,
                status=form.status.data, created_by=current_user)
            flash("Appointment booked.", "success"); return redirect(url_for("appointments.detail", appointment_id=appointment.id))
        except appointment_service.AppointmentServiceError as exc: flash(str(exc), "danger")
    return render_template("appointments/create.html", form=form)


@appointments_bp.get("/<appointment_id>")
@role_required("Receptionist", "Doctor", "Admin", "Patient")
def detail(appointment_id):
    appointment = _get_appointment(appointment_id); _require_view(appointment)
    return render_template("appointments/detail.html", appointment=appointment,
        cancel_form=CancelAppointmentForm(), no_show_form=NoShowForm(), start_form=StartConsultationForm(),
        complete_form=CompleteAppointmentForm(), follow_up_form=FollowUpForm())


@appointments_bp.route("/<appointment_id>/edit", methods=["GET", "POST"])
@role_required("Receptionist", "Admin")
def edit(appointment_id):
    appointment = _get_appointment(appointment_id); form = AppointmentForm(obj=appointment); _form_choices(form)
    form.patient_id.choices = [(appointment.patient_id, f"{appointment.patient.medical_record_number} — {appointment.patient.first_name} {appointment.patient.last_name}")]
    form.status.choices = [(appointment.status, appointment.status.replace("_", " ").title())]
    if form.validate_on_submit():
        try:
            appointment_service.update_appointment(appointment.id, scheduled_start=form.scheduled_start.data, scheduled_end=form.scheduled_end.data,
                doctor_id=form.doctor_id.data or None, department_id=form.department_id.data or None, appointment_type=form.appointment_type.data,
                reason=form.reason.data or "", notes=form.notes.data or "", reception_notes=form.reception_notes.data or "", updated_by=current_user)
            flash("Appointment updated.", "success"); return redirect(url_for("appointments.detail", appointment_id=appointment.id))
        except appointment_service.AppointmentServiceError as exc: flash(str(exc), "danger")
    return render_template("appointments/edit.html", form=form, appointment=appointment)


@appointments_bp.route("/<appointment_id>/cancel", methods=["GET", "POST"])
@role_required("Receptionist", "Admin")
def cancel(appointment_id):
    appointment = _get_appointment(appointment_id); form = CancelAppointmentForm()
    if form.validate_on_submit():
        try:
            appointment_service.cancel_appointment(appointment.id, reason=form.reason.data, cancelled_by=current_user)
            flash("Appointment cancelled.", "success"); return redirect(url_for("appointments.detail", appointment_id=appointment.id))
        except appointment_service.AppointmentServiceError as exc: flash(str(exc), "danger")
    return render_template("appointments/cancel.html", form=form, appointment=appointment)


@appointments_bp.route("/<appointment_id>/reschedule", methods=["GET", "POST"])
@role_required("Receptionist", "Admin")
def reschedule(appointment_id):
    appointment = _get_appointment(appointment_id); form = RescheduleForm(obj=appointment)
    if form.validate_on_submit():
        try:
            appointment_service.reschedule_appointment(appointment.id, scheduled_start=form.scheduled_start.data,
                scheduled_end=form.scheduled_end.data, rescheduled_by=current_user)
            flash("Appointment rescheduled.", "success"); return redirect(url_for("appointments.detail", appointment_id=appointment.id))
        except appointment_service.AppointmentServiceError as exc: flash(str(exc), "danger")
    return render_template("appointments/reschedule.html", form=form, appointment=appointment)


@appointments_bp.get("/today")
@role_required("Receptionist", "Doctor", "Admin", "Patient")
def today():
    doctor_id = current_user.doctor_profile.id if current_user.has_role("Doctor") and current_user.doctor_profile else None
    if current_user.has_role("Doctor") and not doctor_id: abort(403)
    appointments = appointment_service.get_today_appointments(doctor_id=doctor_id)
    if current_user.has_role("Patient"):
        patient = _patient_profile()
        if not patient: abort(403)
        appointments = [a for a in appointments if a.patient_id == patient.id]
    groups = {status: [a for a in appointments if a.status == status] for status in ("arrived", "waiting", "in_consultation", "completed", "no_show")}
    return render_template("appointments/today.html", appointments=appointments, groups=groups)


def _workflow_action(appointment_id, action, success):
    appointment = _get_appointment(appointment_id)
    try:
        action(appointment); flash(success, "success")
    except appointment_service.AppointmentServiceError as exc: flash(str(exc), "danger")
    return redirect(url_for("appointments.detail", appointment_id=appointment.id))


@appointments_bp.post("/<appointment_id>/no-show")
@role_required("Receptionist", "Admin")
def no_show(appointment_id):
    appointment = _get_appointment(appointment_id); form = NoShowForm(); form.appointment_id.data = appointment.id
    if not form.validate_on_submit(): abort(400)
    return _workflow_action(appointment_id, lambda a: appointment_service.mark_no_show(a.id, marked_by=current_user), "Appointment marked no-show.")


@appointments_bp.post("/<appointment_id>/waiting")
@role_required("Receptionist", "Admin")
def waiting(appointment_id):
    return _workflow_action(appointment_id, lambda a: appointment_service.mark_waiting(a.id, marked_by=current_user), "Patient added to the waiting queue.")


@appointments_bp.post("/<appointment_id>/start")
@role_required("Doctor")
def start(appointment_id):
    appointment = _get_appointment(appointment_id); doctor = _require_assigned_doctor(appointment); form = StartConsultationForm(); form.appointment_id.data = appointment.id
    if not form.validate_on_submit(): abort(400)
    try:
        _, visit = appointment_service.start_consultation(appointment.id, doctor_id=doctor.id, started_by=current_user)
        flash("Consultation started.", "success"); return redirect(url_for("emr.visit_detail", visit_id=visit.id))
    except appointment_service.AppointmentServiceError as exc:
        flash(str(exc), "danger"); return redirect(url_for("appointments.detail", appointment_id=appointment.id))


@appointments_bp.post("/<appointment_id>/complete")
@role_required("Doctor")
def complete(appointment_id):
    appointment = _get_appointment(appointment_id); _require_assigned_doctor(appointment); form = CompleteAppointmentForm(); form.appointment_id.data = appointment.id
    if not form.validate_on_submit(): abort(400)
    return _workflow_action(appointment_id, lambda a: appointment_service.complete_appointment(a.id, completed_by=current_user), "Appointment completed.")


@appointments_bp.post("/<appointment_id>/follow-up")
@role_required("Receptionist", "Doctor", "Admin")
def follow_up(appointment_id):
    appointment = _get_appointment(appointment_id); form = FollowUpForm()
    if current_user.has_role("Doctor"): _require_assigned_doctor(appointment)
    if not form.validate_on_submit():
        flash("Enter a valid follow-up date and time.", "danger"); return redirect(url_for("appointments.detail", appointment_id=appointment.id))
    try:
        follow = appointment_service.schedule_follow_up(appointment.id, scheduled_start=form.scheduled_start.data,
            scheduled_end=form.scheduled_end.data, created_by=current_user)
        flash("Follow-up scheduled.", "success"); return redirect(url_for("appointments.detail", appointment_id=follow.id))
    except appointment_service.AppointmentServiceError as exc:
        flash(str(exc), "danger"); return redirect(url_for("appointments.detail", appointment_id=appointment.id))
