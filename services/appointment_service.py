"""Appointment and reception workflow services."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func

from extensions import db
from models import Appointment, AuditLog, Doctor, MedicalRecord, Patient


APPOINTMENT_STATUS_BOOKED = "booked"
APPOINTMENT_STATUS_CONFIRMED = "confirmed"
APPOINTMENT_STATUS_ARRIVED = "arrived"
APPOINTMENT_STATUS_WAITING = "waiting"
APPOINTMENT_STATUS_IN_CONSULTATION = "in_consultation"
APPOINTMENT_STATUS_COMPLETED = "completed"
APPOINTMENT_STATUS_CANCELLED = "cancelled"
APPOINTMENT_STATUS_NO_SHOW = "no_show"
APPOINTMENT_STATUS_FOLLOW_UP_SCHEDULED = "follow_up_scheduled"

ACTIVE_APPOINTMENT_STATUSES = {
    APPOINTMENT_STATUS_BOOKED,
    APPOINTMENT_STATUS_CONFIRMED,
    APPOINTMENT_STATUS_ARRIVED,
    APPOINTMENT_STATUS_WAITING,
    APPOINTMENT_STATUS_IN_CONSULTATION,
}

TERMINAL_APPOINTMENT_STATUSES = {
    APPOINTMENT_STATUS_COMPLETED,
    APPOINTMENT_STATUS_CANCELLED,
    APPOINTMENT_STATUS_NO_SHOW,
}

ALLOWED_STATUS_TRANSITIONS = {
    APPOINTMENT_STATUS_BOOKED: {
        APPOINTMENT_STATUS_CONFIRMED,
        APPOINTMENT_STATUS_ARRIVED,
        APPOINTMENT_STATUS_CANCELLED,
        APPOINTMENT_STATUS_NO_SHOW,
    },
    APPOINTMENT_STATUS_CONFIRMED: {
        APPOINTMENT_STATUS_ARRIVED,
        APPOINTMENT_STATUS_CANCELLED,
        APPOINTMENT_STATUS_NO_SHOW,
    },
    APPOINTMENT_STATUS_ARRIVED: {
        APPOINTMENT_STATUS_WAITING,
        APPOINTMENT_STATUS_CANCELLED,
    },
    APPOINTMENT_STATUS_WAITING: {
        APPOINTMENT_STATUS_IN_CONSULTATION,
        APPOINTMENT_STATUS_CANCELLED,
    },
    APPOINTMENT_STATUS_IN_CONSULTATION: {
        APPOINTMENT_STATUS_COMPLETED,
    },
    APPOINTMENT_STATUS_COMPLETED: set(),
    APPOINTMENT_STATUS_CANCELLED: set(),
    APPOINTMENT_STATUS_NO_SHOW: set(),
    APPOINTMENT_STATUS_FOLLOW_UP_SCHEDULED: set(),
}


class AppointmentServiceError(ValueError):
    """Raised when appointment workflow rules are violated."""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def day_bounds(target_date: date | None = None) -> tuple[datetime, datetime]:
    target_date = target_date or utcnow().date()
    start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


def generate_appointment_number() -> str:
    today = utcnow().strftime("%Y%m%d")
    prefix = f"APT-{today}-"

    count_today = (
        db.session.query(func.count(Appointment.id))
        .filter(Appointment.appointment_number.like(f"{prefix}%"))
        .scalar()
        or 0
    )

    return f"{prefix}{count_today + 1:04d}"


def generate_medical_record_number() -> str:
    today = utcnow().strftime("%Y%m%d")
    prefix = f"MR-{today}-"

    count_today = (
        db.session.query(func.count(MedicalRecord.id))
        .filter(MedicalRecord.record_number.like(f"{prefix}%"))
        .scalar()
        or 0
    )

    return f"{prefix}{count_today + 1:04d}"


def validate_status_transition(current_status: str, new_status: str) -> None:
    if current_status == new_status:
        return

    allowed_targets = ALLOWED_STATUS_TRANSITIONS.get(current_status, set())

    if new_status not in allowed_targets:
        raise AppointmentServiceError(
            f"Invalid appointment status transition: {current_status} → {new_status}"
        )


def get_appointment_or_raise(appointment_id: str) -> Appointment:
    appointment = db.session.get(Appointment, appointment_id)

    if not appointment:
        raise AppointmentServiceError("Appointment not found.")

    return appointment


def get_doctor_department_id(doctor_id: str | None) -> str | None:
    if not doctor_id:
        return None

    doctor = db.session.get(Doctor, doctor_id)

    if not doctor:
        raise AppointmentServiceError("Doctor not found.")

    return doctor.department_id


def next_queue_number(target_date: date | None = None) -> int:
    start, end = day_bounds(target_date)

    max_queue = (
        db.session.query(func.max(Appointment.queue_number))
        .filter(
            Appointment.scheduled_start >= start,
            Appointment.scheduled_start < end,
        )
        .scalar()
        or 0
    )

    return max_queue + 1


def log_appointment_event(
    *,
    action: str,
    appointment: Appointment,
    actor=None,
    outcome: str = "success",
    details: dict | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        actor_user_id=getattr(actor, "id", None),
        action=action,
        resource_type="appointment",
        resource_id=appointment.id,
        outcome=outcome,
        details=details or {},
    )

    db.session.add(audit_log)

    return audit_log


def create_appointment(
    *,
    patient_id: str,
    scheduled_start: datetime,
    doctor_id: str | None = None,
    department_id: str | None = None,
    scheduled_end: datetime | None = None,
    appointment_type: str = "consultation",
    reason: str | None = None,
    notes: str | None = None,
    status: str = APPOINTMENT_STATUS_BOOKED,
    created_by=None,
) -> Appointment:
    patient = db.session.get(Patient, patient_id)

    if not patient:
        raise AppointmentServiceError("Patient not found.")

    if doctor_id:
        department_id = department_id or get_doctor_department_id(doctor_id)

    appointment = Appointment(
        appointment_number=generate_appointment_number(),
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department_id,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        appointment_type=appointment_type,
        status=status,
        reason=reason,
        notes=notes,
    )

    db.session.add(appointment)
    db.session.flush()

    log_appointment_event(
        action="appointment.created",
        appointment=appointment,
        actor=created_by,
        details={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "scheduled_start": scheduled_start.isoformat(),
        },
    )

    db.session.commit()

    return appointment


def update_appointment(
    appointment_id: str,
    *,
    scheduled_start: datetime | None = None,
    scheduled_end: datetime | None = None,
    doctor_id: str | None = None,
    department_id: str | None = None,
    appointment_type: str | None = None,
    reason: str | None = None,
    notes: str | None = None,
    reception_notes: str | None = None,
    updated_by=None,
) -> Appointment:
    appointment = get_appointment_or_raise(appointment_id)

    if appointment.status in TERMINAL_APPOINTMENT_STATUSES:
        raise AppointmentServiceError("Cannot update a closed appointment.")

    if scheduled_start is not None:
        appointment.scheduled_start = scheduled_start

    if scheduled_end is not None:
        appointment.scheduled_end = scheduled_end

    if doctor_id is not None:
        appointment.doctor_id = doctor_id
        appointment.department_id = department_id or get_doctor_department_id(doctor_id)
    elif department_id is not None:
        appointment.department_id = department_id

    if appointment_type is not None:
        appointment.appointment_type = appointment_type

    if reason is not None:
        appointment.reason = reason

    if notes is not None:
        appointment.notes = notes

    if reception_notes is not None:
        appointment.reception_notes = reception_notes

    log_appointment_event(
        action="appointment.updated",
        appointment=appointment,
        actor=updated_by,
        details={
            "appointment_id": appointment.id,
        },
    )

    db.session.commit()

    return appointment


def cancel_appointment(
    appointment_id: str,
    *,
    reason: str | None = None,
    cancelled_by=None,
) -> Appointment:
    appointment = get_appointment_or_raise(appointment_id)

    validate_status_transition(appointment.status, APPOINTMENT_STATUS_CANCELLED)

    appointment.status = APPOINTMENT_STATUS_CANCELLED
    appointment.cancelled_at = utcnow()
    appointment.cancellation_reason = reason
    appointment.cancelled_by_id = getattr(cancelled_by, "id", None)

    log_appointment_event(
        action="appointment.cancelled",
        appointment=appointment,
        actor=cancelled_by,
        details={
            "reason": reason,
        },
    )

    db.session.commit()

    return appointment


def reschedule_appointment(
    appointment_id: str,
    *,
    scheduled_start: datetime,
    scheduled_end: datetime | None = None,
    rescheduled_by=None,
) -> Appointment:
    appointment = get_appointment_or_raise(appointment_id)

    if appointment.status in TERMINAL_APPOINTMENT_STATUSES:
        raise AppointmentServiceError("Cannot reschedule a closed appointment.")

    appointment.scheduled_start = scheduled_start
    appointment.scheduled_end = scheduled_end

    if appointment.status == APPOINTMENT_STATUS_NO_SHOW:
        appointment.status = APPOINTMENT_STATUS_BOOKED

    log_appointment_event(
        action="appointment.rescheduled",
        appointment=appointment,
        actor=rescheduled_by,
        details={
            "scheduled_start": scheduled_start.isoformat(),
        },
    )

    db.session.commit()

    return appointment


def mark_arrived(
    appointment_id: str,
    *,
    reception_notes: str | None = None,
    marked_by=None,
) -> Appointment:
    appointment = get_appointment_or_raise(appointment_id)

    if appointment.status not in {
        APPOINTMENT_STATUS_BOOKED,
        APPOINTMENT_STATUS_CONFIRMED,
    }:
        raise AppointmentServiceError("Only booked or confirmed appointments can arrive.")

    validate_status_transition(appointment.status, APPOINTMENT_STATUS_ARRIVED)

    appointment.status = APPOINTMENT_STATUS_ARRIVED
    appointment.arrival_time = utcnow()
    appointment.reception_notes = reception_notes or appointment.reception_notes
    appointment.queue_number = next_queue_number(appointment.scheduled_start.date())

    log_appointment_event(
        action="appointment.arrived",
        appointment=appointment,
        actor=marked_by,
        details={
            "queue_number": appointment.queue_number,
        },
    )

    db.session.commit()

    return appointment


def mark_waiting(appointment_id: str, *, marked_by=None) -> Appointment:
    appointment = get_appointment_or_raise(appointment_id)

    validate_status_transition(appointment.status, APPOINTMENT_STATUS_WAITING)

    appointment.status = APPOINTMENT_STATUS_WAITING

    if not appointment.queue_number:
        appointment.queue_number = next_queue_number(appointment.scheduled_start.date())

    log_appointment_event(
        action="appointment.waiting",
        appointment=appointment,
        actor=marked_by,
        details={
            "queue_number": appointment.queue_number,
        },
    )

    db.session.commit()

    return appointment


def mark_no_show(appointment_id: str, *, marked_by=None) -> Appointment:
    appointment = get_appointment_or_raise(appointment_id)

    validate_status_transition(appointment.status, APPOINTMENT_STATUS_NO_SHOW)

    appointment.status = APPOINTMENT_STATUS_NO_SHOW

    log_appointment_event(
        action="appointment.no_show",
        appointment=appointment,
        actor=marked_by,
    )

    db.session.commit()

    return appointment


def get_or_create_medical_record_for_appointment(
    appointment: Appointment,
    *,
    doctor_id: str | None = None,
) -> MedicalRecord:
    existing = MedicalRecord.query.filter_by(appointment_id=appointment.id).first()

    if existing:
        return existing

    medical_record = MedicalRecord(
        record_number=generate_medical_record_number(),
        patient_id=appointment.patient_id,
        doctor_id=doctor_id,
        appointment_id=appointment.id,
        encounter_type="outpatient",
        encounter_at=utcnow(),
        chief_complaint=appointment.reason,
        status="draft",
    )

    db.session.add(medical_record)
    db.session.flush()

    return medical_record


def start_consultation(
    appointment_id: str,
    *,
    doctor_id: str | None = None,
    started_by=None,
) -> tuple[Appointment, MedicalRecord]:
    appointment = get_appointment_or_raise(appointment_id)

    if appointment.status == APPOINTMENT_STATUS_ARRIVED:
        appointment.status = APPOINTMENT_STATUS_WAITING

    validate_status_transition(appointment.status, APPOINTMENT_STATUS_IN_CONSULTATION)

    appointment.status = APPOINTMENT_STATUS_IN_CONSULTATION
    appointment.consultation_started_at = utcnow()

    medical_record = get_or_create_medical_record_for_appointment(
        appointment,
        doctor_id=doctor_id or appointment.doctor_id,
    )

    log_appointment_event(
        action="appointment.consultation_started",
        appointment=appointment,
        actor=started_by,
        details={
            "medical_record_id": medical_record.id,
        },
    )

    db.session.commit()

    return appointment, medical_record


def complete_appointment(
    appointment_id: str,
    *,
    completed_by=None,
) -> Appointment:
    appointment = get_appointment_or_raise(appointment_id)

    validate_status_transition(appointment.status, APPOINTMENT_STATUS_COMPLETED)

    appointment.status = APPOINTMENT_STATUS_COMPLETED
    appointment.consultation_completed_at = utcnow()

    log_appointment_event(
        action="appointment.completed",
        appointment=appointment,
        actor=completed_by,
    )

    db.session.commit()

    return appointment


def schedule_follow_up(
    appointment_id: str,
    *,
    scheduled_start: datetime,
    scheduled_end: datetime | None = None,
    doctor_id: str | None = None,
    created_by=None,
) -> Appointment:
    original = get_appointment_or_raise(appointment_id)

    follow_up = create_appointment(
        patient_id=original.patient_id,
        doctor_id=doctor_id or original.doctor_id,
        department_id=original.department_id,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        appointment_type="follow_up",
        reason="Follow-up visit",
        status=APPOINTMENT_STATUS_BOOKED,
        created_by=created_by,
    )

    follow_up.follow_up_of_id = original.id
    original.status = APPOINTMENT_STATUS_FOLLOW_UP_SCHEDULED

    log_appointment_event(
        action="appointment.follow_up_scheduled",
        appointment=follow_up,
        actor=created_by,
        details={
            "original_appointment_id": original.id,
        },
    )

    db.session.commit()

    return follow_up


def get_today_appointments(
    *,
    target_date: date | None = None,
    doctor_id: str | None = None,
    department_id: str | None = None,
):
    start, end = day_bounds(target_date)

    query = Appointment.query.filter(
        Appointment.scheduled_start >= start,
        Appointment.scheduled_start < end,
    )

    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)

    if department_id:
        query = query.filter(Appointment.department_id == department_id)

    return query.order_by(Appointment.scheduled_start.asc()).all()


def get_waiting_queue(
    *,
    target_date: date | None = None,
    doctor_id: str | None = None,
    department_id: str | None = None,
):
    start, end = day_bounds(target_date)

    query = Appointment.query.filter(
        Appointment.scheduled_start >= start,
        Appointment.scheduled_start < end,
        Appointment.status.in_(
            [
                APPOINTMENT_STATUS_ARRIVED,
                APPOINTMENT_STATUS_WAITING,
                APPOINTMENT_STATUS_IN_CONSULTATION,
            ]
        ),
    )

    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)

    if department_id:
        query = query.filter(Appointment.department_id == department_id)

    return query.order_by(
        Appointment.queue_number.asc(),
        Appointment.arrival_time.asc(),
    ).all()


def prevent_duplicate_patient(
    *,
    first_name: str,
    last_name: str,
    phone: str | None = None,
    date_of_birth: date | None = None,
):
    query = Patient.query.filter(
        func.lower(Patient.first_name) == first_name.strip().lower(),
        func.lower(Patient.last_name) == last_name.strip().lower(),
    )

    if phone:
        query = query.filter(Patient.phone == phone)

    if date_of_birth:
        query = query.filter(Patient.date_of_birth == date_of_birth)

    return query.first()