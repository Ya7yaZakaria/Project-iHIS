"""Front-desk registration, check-in, queue, walk-in, follow-up, and billing routes."""
from datetime import date
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from auth.decorators import login_required
from extensions import db
from models import Appointment, Doctor, Patient
from reception.forms import (
    BillingInitiationForm,
    FollowUpBookingForm,
    QueueReorderForm,
    QueueStatusForm,
    ReceptionCheckInForm,
    ReceptionPatientRegistrationForm,
    ReceptionPatientSearchForm,
    WalkInForm,
)
from services.reception_service import (
    ReceptionServiceError,
    book_follow_up,
    check_in_patient,
    create_walk_in_visit,
    get_reception_dashboard,
    get_today_queue,
    initiate_billing_placeholder,
    prevent_duplicate_patient,
    register_patient_from_reception,
    reorder_queue,
    search_patient_for_reception,
    update_queue_status,
)

reception_bp = Blueprint("reception", __name__, url_prefix="/reception")


def _can_view_reception():
    return current_user.has_role(
        "Super Admin",
        "Admin",
        "Receptionist",
        "Doctor",
        "Women’s Health Doctor",
    )


def _can_manage_reception():
    return current_user.has_role(
        "Super Admin",
        "Admin",
        "Receptionist",
    )


def _blank_choice(label="Not selected"):
    return [("", label)]


def _patient_choices(include_blank=True):
    patients = db.session.scalars(
        db.select(Patient)
        .where(Patient.deleted_at.is_(None))
        .order_by(Patient.last_name, Patient.first_name)
        .limit(200)
    ).all()

    choices = [
        (
            patient.id,
            f"{patient.medical_record_number} · {patient.first_name} {patient.last_name}",
        )
        for patient in patients
    ]

    return (_blank_choice("Select patient") if include_blank else []) + choices


def _appointment_choices(patient_id=None, include_blank=True):
    statement = db.select(Appointment).where(Appointment.deleted_at.is_(None))

    if patient_id:
        statement = statement.where(Appointment.patient_id == patient_id)

    appointments = db.session.scalars(
        statement.order_by(Appointment.scheduled_start.desc()).limit(200)
    ).all()

    choices = [
        (
            appointment.id,
            (
                f"{appointment.scheduled_start.strftime('%Y-%m-%d %H:%M')} · "
                f"{appointment.patient.first_name} {appointment.patient.last_name} · "
                f"{appointment.status.replace('_', ' ').title()}"
            ),
        )
        for appointment in appointments
    ]

    return (_blank_choice("No linked appointment") if include_blank else []) + choices


def _today_check_in_choices():
    appointments = db.session.scalars(
        db.select(Appointment)
        .where(
            Appointment.deleted_at.is_(None),
            Appointment.status.in_(("booked", "confirmed")),
        )
        .order_by(Appointment.scheduled_start)
    ).all()

    return _blank_choice("Select today appointment") + [
        (
            appointment.id,
            (
                f"{appointment.scheduled_start.strftime('%H:%M')} · "
                f"{appointment.patient.first_name} {appointment.patient.last_name} · "
                f"{appointment.appointment_number}"
            ),
        )
        for appointment in appointments
    ]


def _doctor_choices():
    doctors = db.session.scalars(
        db.select(Doctor)
        .where(Doctor.deleted_at.is_(None))
        .order_by(Doctor.created_at.desc())
        .limit(200)
    ).all()

    return _blank_choice("Unassigned") + [
        (
            doctor.id,
            doctor.user.full_name if doctor.user else f"Doctor {doctor.id}",
        )
        for doctor in doctors
    ]


@reception_bp.get("")
@reception_bp.get("/")
@login_required
def dashboard():
    if not _can_view_reception():
        abort(403)

    if current_user.has_role("Doctor", "Women’s Health Doctor") and not current_user.has_role(
        "Super Admin",
        "Admin",
        "Receptionist",
    ):
        return redirect(url_for("reception.queue"))

    dashboard_data = get_reception_dashboard(current_user)

    return render_template(
        "reception/dashboard.html",
        dashboard=dashboard_data,
    )


@reception_bp.route("/register-patient", methods=["GET", "POST"])
@login_required
def register_patient():
    if not _can_manage_reception():
        abort(403)

    form = ReceptionPatientRegistrationForm()
    duplicate = None

    if form.validate_on_submit():
        duplicate = prevent_duplicate_patient(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            email=form.email.data,
            date_of_birth=form.date_of_birth.data,
        )

        if duplicate:
            flash("Possible duplicate patient found. Review before creating a new record.", "warning")
            return render_template(
                "reception/register_patient.html",
                form=form,
                duplicate=duplicate,
            )

        try:
            patient = register_patient_from_reception(
                actor=current_user,
                medical_record_number=form.medical_record_number.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                date_of_birth=form.date_of_birth.data,
                sex_at_birth=form.sex_at_birth.data,
                phone=form.phone.data,
                email=form.email.data,
                address=form.address.data,
            )
            flash("Patient registered from reception.", "success")
            return redirect(url_for("reception.search_patient", query=patient.medical_record_number))
        except (ReceptionServiceError, PermissionError) as exc:
            flash(str(exc), "danger")

    return render_template(
        "reception/register_patient.html",
        form=form,
        duplicate=duplicate,
    )


@reception_bp.route("/search-patient", methods=["GET", "POST"])
@login_required
def search_patient():
    if not _can_manage_reception():
        abort(403)

    form = ReceptionPatientSearchForm(request.args if request.method == "GET" else None)
    results = []

    query = request.args.get("query")
    phone = request.args.get("phone")
    date_of_birth = None

    if request.method == "POST":
        form = ReceptionPatientSearchForm()
        if form.validate_on_submit():
            query = form.query.data
            phone = form.phone.data
            date_of_birth = form.date_of_birth.data
            return redirect(
                url_for(
                    "reception.search_patient",
                    query=query or "",
                    phone=phone or "",
                    date_of_birth=date_of_birth.isoformat() if date_of_birth else "",
                )
            )

    dob_arg = request.args.get("date_of_birth")
    if dob_arg:
        try:
            date_of_birth = date.fromisoformat(dob_arg)
        except ValueError:
            date_of_birth = None

    if query or phone or request.args.get("date_of_birth"):
        results = search_patient_for_reception(
            actor=current_user,
            query=query,
            phone=phone,
            date_of_birth=date_of_birth,
        )

    return render_template(
        "reception/search_patient.html",
        form=form,
        results=results,
    )


@reception_bp.route("/check-in", methods=["GET", "POST"])
@login_required
def check_in():
    if not _can_manage_reception():
        abort(403)

    form = ReceptionCheckInForm()
    form.appointment_id.choices = _today_check_in_choices()

    if form.validate_on_submit():
        try:
            appointment = check_in_patient(
                actor=current_user,
                appointment_id=form.appointment_id.data,
                reception_notes=form.reception_notes.data,
            )
            flash(
                f"{appointment.patient.first_name} checked in as queue #{appointment.queue_number}.",
                "success",
            )
            return redirect(url_for("reception.queue"))
        except (ReceptionServiceError, PermissionError, ValueError) as exc:
            flash(str(exc), "danger")

    return render_template(
        "reception/check_in.html",
        form=form,
    )


@reception_bp.route("/queue", methods=["GET", "POST"])
@login_required
def queue():
    if not _can_view_reception():
        abort(403)

    if request.method == "POST":
        if not _can_manage_reception():
            abort(403)

        action = request.form.get("action")

        if action == "status":
            form = QueueStatusForm()
            if form.validate_on_submit():
                try:
                    update_queue_status(
                        actor=current_user,
                        appointment_id=form.appointment_id.data,
                        status=form.status.data,
                        reception_notes=form.reception_notes.data,
                    )
                    flash("Queue status updated.", "success")
                except (ReceptionServiceError, PermissionError, ValueError) as exc:
                    flash(str(exc), "danger")

        elif action == "reorder":
            form = QueueReorderForm()
            if form.validate_on_submit():
                try:
                    reorder_queue(
                        actor=current_user,
                        appointment_id=form.appointment_id.data,
                        queue_number=form.queue_number.data,
                    )
                    flash("Queue reordered.", "success")
                except (ReceptionServiceError, PermissionError, ValueError) as exc:
                    flash(str(exc), "danger")

        return redirect(url_for("reception.queue"))

    doctor_id = None
    if current_user.has_role("Doctor", "Women’s Health Doctor") and getattr(current_user, "doctor_profile", None):
        doctor_id = current_user.doctor_profile.id

    appointments = get_today_queue(
        current_user,
        doctor_id=doctor_id,
    )

    return render_template(
        "reception/queue.html",
        appointments=appointments,
        status_form=QueueStatusForm(),
        reorder_form=QueueReorderForm(),
    )


@reception_bp.route("/walk-in", methods=["GET", "POST"])
@login_required
def walk_in():
    if not _can_manage_reception():
        abort(403)

    form = WalkInForm()
    form.patient_id.choices = _patient_choices(include_blank=True)

    if form.validate_on_submit():
        try:
            appointment = create_walk_in_visit(
                actor=current_user,
                patient_id=form.patient_id.data or None,
                medical_record_number=form.medical_record_number.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                date_of_birth=form.date_of_birth.data,
                sex_at_birth=form.sex_at_birth.data,
                phone=form.phone.data,
                reason=form.reason.data,
                reception_notes=form.reception_notes.data,
            )
            flash(
                f"Walk-in created as queue #{appointment.queue_number}.",
                "success",
            )
            return redirect(url_for("reception.queue"))
        except (ReceptionServiceError, PermissionError, ValueError) as exc:
            flash(str(exc), "danger")

    return render_template(
        "reception/walk_in.html",
        form=form,
    )


@reception_bp.route("/follow-up", methods=["GET", "POST"])
@login_required
def follow_up():
    if not _can_manage_reception():
        abort(403)

    form = FollowUpBookingForm()
    form.patient_id.choices = _patient_choices(include_blank=True)
    selected_patient_id = request.form.get("patient_id") or request.args.get("patient_id")
    form.follow_up_of_id.choices = _appointment_choices(selected_patient_id, include_blank=True)
    form.doctor_id.choices = _doctor_choices()

    if form.validate_on_submit():
        try:
            appointment = book_follow_up(
                actor=current_user,
                patient_id=form.patient_id.data,
                scheduled_start=form.scheduled_start.data,
                follow_up_of_id=form.follow_up_of_id.data or None,
                doctor_id=form.doctor_id.data or None,
                reason=form.reason.data,
                notes=form.notes.data,
            )
            flash("Follow-up appointment booked.", "success")
            return redirect(url_for("appointments.detail", appointment_id=appointment.id))
        except (ReceptionServiceError, PermissionError, ValueError) as exc:
            flash(str(exc), "danger")

    return render_template(
        "reception/follow_up.html",
        form=form,
    )


@reception_bp.route("/billing-initiation", methods=["GET", "POST"])
@login_required
def billing_initiation():
    if not _can_manage_reception():
        abort(403)

    form = BillingInitiationForm()
    form.patient_id.choices = _patient_choices(include_blank=True)
    selected_patient_id = request.form.get("patient_id") or request.args.get("patient_id")
    form.appointment_id.choices = _appointment_choices(selected_patient_id, include_blank=True)

    if form.validate_on_submit():
        try:
            billing = initiate_billing_placeholder(
                actor=current_user,
                patient_id=form.patient_id.data,
                appointment_id=form.appointment_id.data or None,
                status=form.status.data,
                notes=form.notes.data,
            )
            flash(f"Billing placeholder started with status: {billing.status}.", "success")
            return redirect(url_for("reception.dashboard"))
        except (ReceptionServiceError, PermissionError, ValueError) as exc:
            flash(str(exc), "danger")

    return render_template(
        "reception/billing_initiation.html",
        form=form,
    )