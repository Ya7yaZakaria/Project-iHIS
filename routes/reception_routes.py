"""Front-desk registration, check-in, and clinic queue routes."""

from collections import Counter

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user

from appointments.forms import CheckInForm
from auth.decorators import role_required
from emr.forms import PatientForm, lines
from extensions import db
from services import appointment_service
from services.emr_service import create_patient

reception_bp = Blueprint("reception", __name__, url_prefix="/reception")


def _history(form):
    names = ("allergies", "chronic_conditions", "surgical_history", "family_history", "vaccination_history")
    return {name: lines(getattr(form, name).data) for name in names}


@reception_bp.get("")
@reception_bp.get("/")
@role_required("Receptionist", "Admin")
def dashboard():
    appointments = appointment_service.get_today_appointments()
    counts = Counter(item.status for item in appointments)
    next_appointment = next((item for item in appointments if item.status in appointment_service.ACTIVE_APPOINTMENT_STATUSES), None)
    doctor_schedule = Counter(
        item.doctor.user.full_name if item.doctor and item.doctor.user else "Unassigned"
        for item in appointments
    )
    return render_template("reception/dashboard.html", appointments=appointments, counts=counts,
        next_appointment=next_appointment, doctor_schedule=doctor_schedule)


@reception_bp.route("/register-patient", methods=["GET", "POST"])
@role_required("Receptionist", "Admin")
def register_patient():
    form = PatientForm()
    if form.validate_on_submit():
        duplicate = appointment_service.prevent_duplicate_patient(first_name=form.first_name.data,
            last_name=form.last_name.data, phone=form.phone.data or None, date_of_birth=form.date_of_birth.data)
        if duplicate:
            flash("A matching patient already exists. Review the existing record before registering another.", "warning")
            return render_template("patients/create.html", form=form, duplicate=duplicate)
        try:
            patient = create_patient(actor=current_user, first_name=form.first_name.data, last_name=form.last_name.data,
                date_of_birth=form.date_of_birth.data, sex_at_birth=form.sex_at_birth.data,
                medical_record_number=form.medical_record_number.data, blood_type=form.blood_type.data or None,
                phone=form.phone.data or None, email=form.email.data or None, address=form.address.data or None, **_history(form))
            flash("Patient registered.", "success")
            return redirect(url_for("appointments.create", patient_id=patient.id))
        except (ValueError, PermissionError) as exc: flash(str(exc), "danger")
    return render_template("patients/create.html", form=form, reception_registration=True)


@reception_bp.route("/check-in", methods=["GET", "POST"])
@role_required("Receptionist", "Admin")
def check_in():
    form = CheckInForm()
    appointments = [item for item in appointment_service.get_today_appointments()
                    if item.status in {"booked", "confirmed"}]
    if form.validate_on_submit():
        if form.appointment_id.data not in {item.id for item in appointments}:
            flash("Only today's booked or confirmed appointments can be checked in.", "danger")
            return render_template("reception/check_in.html", form=form, appointments=appointments), 400
        try:
            appointment = appointment_service.mark_arrived(form.appointment_id.data,
                reception_notes=form.reception_notes.data or None, marked_by=current_user)
            flash(f"{appointment.patient.first_name} checked in as queue #{appointment.queue_number}.", "success")
            return redirect(url_for("reception.queue"))
        except appointment_service.AppointmentServiceError as exc: flash(str(exc), "danger")
    return render_template("reception/check_in.html", form=form, appointments=appointments)


@reception_bp.get("/queue")
@role_required("Receptionist", "Doctor", "Admin")
def queue():
    doctor_id = current_user.doctor_profile.id if current_user.has_role("Doctor") and current_user.doctor_profile else None
    if current_user.has_role("Doctor") and not doctor_id: return redirect(url_for("appointments.index"))
    appointments = appointment_service.get_waiting_queue(doctor_id=doctor_id)
    return render_template("reception/queue.html", appointments=appointments)
