"""Service layer for Phase 14 Reception module."""

from datetime import datetime, time, timedelta, timezone

from sqlalchemy import or_

from extensions import db
from models import Appointment, AuditLog, BillingInitiation, Doctor, Patient
from services import appointment_service


class ReceptionServiceError(ValueError):
    """Raised when reception workflow validation fails."""


BILLING_STATUSES = {"not_started", "pending", "paid", "cancelled"}

QUEUE_STATUSES = {
    "waiting",
    "called",
    "in_consultation",
    "completed",
    "cancelled",
    "no_show",
}


def _now():
    return datetime.now(timezone.utc)


def _is_blank(value):
    return value is None or value == ""


def _clean(value):
    return value or None


def _require_reception_access(actor):
    if actor is None or not actor.is_authenticated:
        raise PermissionError("Login is required.")

    if not actor.has_role("Super Admin", "Admin", "Receptionist"):
        raise PermissionError("Reception access is required.")


def _require_queue_view(actor):
    if actor is None or not actor.is_authenticated:
        raise PermissionError("Login is required.")

    if not actor.has_role("Super Admin", "Admin", "Receptionist", "Doctor", "Women’s Health Doctor"):
        raise PermissionError("Reception queue view access is required.")


def _audit(action, actor, resource_type, resource_id=None, details=None):
    db.session.add(
        AuditLog(
            actor_user_id=getattr(actor, "id", None),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome="success",
            details=details or {},
        )
    )


def _patient_or_error(patient_id):
    patient = db.session.get(Patient, patient_id)
    if patient is None or patient.is_deleted:
        raise ReceptionServiceError("Patient not found.")
    return patient


def _appointment_or_error(appointment_id):
    appointment = db.session.get(Appointment, appointment_id)
    if appointment is None or appointment.is_deleted:
        raise ReceptionServiceError("Appointment not found.")
    return appointment


def _today_bounds():
    today = _now().date()
    start = datetime.combine(today, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


def prevent_duplicate_patient(
    *,
    first_name=None,
    last_name=None,
    phone=None,
    date_of_birth=None,
    email=None,
):
    """Find likely duplicate patient.

    Uses practical matching:
    - same phone if provided
    - same first name + last name + DOB
    - same email if provided
    """
    filters = [Patient.deleted_at.is_(None)]

    duplicate_conditions = []

    if phone:
        duplicate_conditions.append(Patient.phone == phone)

    if email:
        duplicate_conditions.append(Patient.email == email)

    if first_name and last_name and date_of_birth:
        duplicate_conditions.append(
            db.and_(
                Patient.first_name.ilike(first_name.strip()),
                Patient.last_name.ilike(last_name.strip()),
                Patient.date_of_birth == date_of_birth,
            )
        )

    if not duplicate_conditions:
        return None

    return db.session.scalars(
        db.select(Patient)
        .where(*filters)
        .where(or_(*duplicate_conditions))
        .order_by(Patient.created_at.desc())
        .limit(1)
    ).first()


def register_patient_from_reception(
    *,
    actor,
    medical_record_number,
    first_name,
    last_name,
    date_of_birth,
    sex_at_birth,
    phone=None,
    email=None,
    address=None,
):
    _require_reception_access(actor)

    duplicate = prevent_duplicate_patient(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        date_of_birth=date_of_birth,
    )
    if duplicate:
        raise ReceptionServiceError("Possible duplicate patient found.")

    existing_mrn = db.session.scalars(
        db.select(Patient).where(Patient.medical_record_number == medical_record_number)
    ).first()
    if existing_mrn:
        raise ReceptionServiceError("Medical record number already exists.")

    patient = Patient(
        medical_record_number=medical_record_number.strip(),
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        date_of_birth=date_of_birth,
        sex_at_birth=sex_at_birth,
        phone=_clean(phone),
        email=_clean(email),
        address=_clean(address),
    )

    db.session.add(patient)
    db.session.flush()

    _audit(
        "reception.patient_registered",
        actor,
        "Patient",
        patient.id,
        {"medical_record_number": patient.medical_record_number},
    )

    db.session.commit()
    return patient


def update_patient_demographics_from_reception(
    *,
    actor,
    patient_id,
    first_name,
    last_name,
    date_of_birth,
    sex_at_birth,
    phone=None,
    email=None,
    address=None,
):
    _require_reception_access(actor)

    patient = _patient_or_error(patient_id)
    patient.first_name = first_name.strip()
    patient.last_name = last_name.strip()
    patient.date_of_birth = date_of_birth
    patient.sex_at_birth = sex_at_birth
    patient.phone = _clean(phone)
    patient.email = _clean(email)
    patient.address = _clean(address)

    _audit(
        "reception.demographics_updated",
        actor,
        "Patient",
        patient.id,
        {"patient_id": patient.id},
    )

    db.session.commit()
    return patient


def search_patient_for_reception(*, actor, query=None, phone=None, date_of_birth=None, limit=25):
    _require_reception_access(actor)

    statement = db.select(Patient).where(Patient.deleted_at.is_(None))

    if query:
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                Patient.first_name.ilike(pattern),
                Patient.last_name.ilike(pattern),
                Patient.medical_record_number.ilike(pattern),
                Patient.phone.ilike(pattern),
                Patient.email.ilike(pattern),
            )
        )

    if phone:
        statement = statement.where(Patient.phone.ilike(f"%{phone.strip()}%"))

    if date_of_birth:
        statement = statement.where(Patient.date_of_birth == date_of_birth)

    return db.session.scalars(
        statement.order_by(Patient.created_at.desc()).limit(limit)
    ).all()


def get_reception_dashboard(actor):
    _require_reception_access(actor)

    start, end = _today_bounds()

    appointments = db.session.scalars(
        db.select(Appointment)
        .where(
            Appointment.deleted_at.is_(None),
            Appointment.scheduled_start >= start,
            Appointment.scheduled_start < end,
        )
        .order_by(Appointment.scheduled_start, Appointment.queue_number)
    ).all()

    waiting = [item for item in appointments if item.status == "waiting"]
    checked_in = [item for item in appointments if item.status in {"arrived", "waiting", "in_consultation"}]
    no_shows = [item for item in appointments if item.status == "no_show"]
    walk_ins = [item for item in appointments if item.appointment_type == "walk_in"]
    follow_ups = [item for item in appointments if item.appointment_type == "follow_up"]

    return {
        "appointments": appointments,
        "waiting": waiting,
        "checked_in": checked_in,
        "no_shows": no_shows,
        "walk_ins": walk_ins,
        "follow_ups": follow_ups,
        "counts": {
            "daily_appointments": len(appointments),
            "waiting": len(waiting),
            "checked_in": len(checked_in),
            "no_shows": len(no_shows),
            "walk_ins": len(walk_ins),
            "follow_ups": len(follow_ups),
        },
    }


def get_today_queue(actor, *, doctor_id=None, department_id=None):
    _require_queue_view(actor)

    start, end = _today_bounds()

    statement = db.select(Appointment).where(
        Appointment.deleted_at.is_(None),
        Appointment.scheduled_start >= start,
        Appointment.scheduled_start < end,
        Appointment.status.in_(("arrived", "waiting", "called", "in_consultation")),
    )

    if doctor_id:
        statement = statement.where(Appointment.doctor_id == doctor_id)

    if department_id:
        statement = statement.where(Appointment.department_id == department_id)

    return db.session.scalars(
        statement.order_by(Appointment.queue_number, Appointment.arrival_time, Appointment.scheduled_start)
    ).all()


def check_in_patient(*, actor, appointment_id, reception_notes=None):
    _require_reception_access(actor)

    appointment = appointment_service.mark_arrived(
        appointment_id,
        reception_notes=_clean(reception_notes),
        marked_by=actor,
    )

    _audit(
        "reception.check_in",
        actor,
        "Appointment",
        appointment.id,
        {"queue_number": appointment.queue_number},
    )

    db.session.commit()
    return appointment


def add_patient_to_queue(*, actor, appointment_id):
    _require_reception_access(actor)

    appointment = appointment_service.mark_waiting(
        appointment_id,
        marked_by=actor,
    )

    _audit(
        "reception.queue_added",
        actor,
        "Appointment",
        appointment.id,
        {"queue_number": appointment.queue_number},
    )

    db.session.commit()
    return appointment


def update_queue_status(*, actor, appointment_id, status, reception_notes=None):
    _require_reception_access(actor)

    if status not in QUEUE_STATUSES:
        raise ReceptionServiceError("Queue status is invalid.")

    appointment = _appointment_or_error(appointment_id)

    if status == "called":
        # Placeholder status used by reception UI.
        # It is not in appointment_service transitions yet, so set directly.
        appointment.status = "called"
    elif status == "waiting":
        if appointment.status == "arrived":
            appointment = appointment_service.mark_waiting(appointment_id, marked_by=actor)
        else:
            appointment.status = "waiting"
    elif status == "in_consultation":
        appointment.status = "in_consultation"
        appointment.consultation_started_at = appointment.consultation_started_at or _now()
    elif status == "completed":
        appointment.status = "completed"
        appointment.consultation_completed_at = appointment.consultation_completed_at or _now()
    elif status == "cancelled":
        appointment = appointment_service.cancel_appointment(
            appointment_id,
            reason=reception_notes,
            cancelled_by=actor,
        )
    elif status == "no_show":
        appointment = appointment_service.mark_no_show(
            appointment_id,
            marked_by=actor,
        )

    if reception_notes:
        appointment.reception_notes = reception_notes

    _audit(
        "reception.queue_status_updated",
        actor,
        "Appointment",
        appointment.id,
        {"status": status},
    )

    db.session.commit()
    return appointment


def reorder_queue(*, actor, appointment_id, queue_number):
    _require_reception_access(actor)

    appointment = _appointment_or_error(appointment_id)

    try:
        queue_number = int(queue_number)
    except (TypeError, ValueError):
        raise ReceptionServiceError("queue_number must be a number")

    if queue_number <= 0:
        raise ReceptionServiceError("queue_number must be positive")

    appointment.queue_number = queue_number

    _audit(
        "reception.queue_reordered",
        actor,
        "Appointment",
        appointment.id,
        {"queue_number": queue_number},
    )

    db.session.commit()
    return appointment


def book_follow_up(
    *,
    actor,
    patient_id,
    scheduled_start,
    follow_up_of_id=None,
    doctor_id=None,
    reason=None,
    notes=None,
):
    _require_reception_access(actor)

    patient = _patient_or_error(patient_id)

    department_id = None
    if doctor_id:
        doctor = db.session.get(Doctor, doctor_id)
        if doctor is None:
            raise ReceptionServiceError("Doctor not found.")
        department_id = doctor.department_id

    appointment = appointment_service.create_appointment(
        patient_id=patient.id,
        scheduled_start=scheduled_start,
        doctor_id=_clean(doctor_id),
        department_id=department_id,
        appointment_type="follow_up",
        reason=_clean(reason),
        notes=_clean(notes),
        created_by=actor,
    )

    if follow_up_of_id:
        original = _appointment_or_error(follow_up_of_id)
        if original.patient_id != patient.id:
            raise ReceptionServiceError("Follow-up appointment must belong to same patient.")
        appointment.follow_up_of_id = original.id

    _audit(
        "reception.follow_up_booked",
        actor,
        "Appointment",
        appointment.id,
        {"patient_id": patient.id, "follow_up_of_id": follow_up_of_id},
    )

    db.session.commit()
    return appointment


def create_walk_in_visit(
    *,
    actor,
    patient_id=None,
    medical_record_number=None,
    first_name=None,
    last_name=None,
    date_of_birth=None,
    sex_at_birth=None,
    phone=None,
    reason=None,
    reception_notes=None,
):
    _require_reception_access(actor)

    if patient_id:
        patient = _patient_or_error(patient_id)
    else:
        if not all([medical_record_number, first_name, last_name, date_of_birth, sex_at_birth]):
            raise ReceptionServiceError("New walk-in patient requires file number, name, DOB, and sex.")

        patient = register_patient_from_reception(
            actor=actor,
            medical_record_number=medical_record_number,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            sex_at_birth=sex_at_birth,
            phone=phone,
        )

    appointment = appointment_service.create_appointment(
        patient_id=patient.id,
        scheduled_start=_now(),
        appointment_type="walk_in",
        reason=_clean(reason),
        notes=_clean(reception_notes),
        status=appointment_service.APPOINTMENT_STATUS_BOOKED,
        created_by=actor,
    )

    appointment = appointment_service.mark_arrived(
        appointment.id,
        reception_notes=_clean(reception_notes),
        marked_by=actor,
    )

    _audit(
        "reception.walk_in_created",
        actor,
        "Appointment",
        appointment.id,
        {"patient_id": patient.id, "queue_number": appointment.queue_number},
    )

    db.session.commit()
    return appointment


def initiate_billing_placeholder(
    *,
    actor,
    patient_id,
    appointment_id=None,
    status="pending",
    notes=None,
):
    _require_reception_access(actor)

    if status not in BILLING_STATUSES:
        raise ReceptionServiceError("Billing status is invalid.")

    patient = _patient_or_error(patient_id)

    appointment = None
    if appointment_id:
        appointment = _appointment_or_error(appointment_id)
        if appointment.patient_id != patient.id:
            raise ReceptionServiceError("Appointment does not belong to selected patient.")

    billing = BillingInitiation(
        patient_id=patient.id,
        appointment_id=getattr(appointment, "id", None),
        status=status,
        started_by_id=actor.id,
        notes=_clean(notes),
    )

    db.session.add(billing)
    db.session.flush()

    _audit(
        "reception.billing_initiated",
        actor,
        "BillingInitiation",
        billing.id,
        {"patient_id": patient.id, "appointment_id": appointment_id, "status": status},
    )

    db.session.commit()
    return billing