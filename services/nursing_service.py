"""Simple business services for the Nursing module."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from extensions import db
from models import (
    Appointment,
    AuditLog,
    MedicalRecord,
    MedicationAdministration,
    NursingCarePlan,
    NursingNote,
    Patient,
    VitalSign,
)


class NursingServiceError(ValueError):
    """Raised when nursing validation fails."""


def _now():
    return datetime.now(timezone.utc)


def _is_blank(value):
    return value is None or value == ""


def _require_patient(patient_id):
    if not patient_id:
        raise NursingServiceError("patient_id is required")

    patient = db.session.get(Patient, patient_id)
    if patient is None or patient.is_deleted:
        raise NursingServiceError("patient_id is invalid")

    return patient


def _require_nursing_write(actor):
    if actor is None or not actor.is_authenticated:
        raise PermissionError("Login is required.")

    if not actor.has_role("Super Admin", "Admin", "Nurse", "Doctor", "Women’s Health Doctor"):
        raise PermissionError("Nursing write access is required.")


def _require_nursing_view(actor):
    if actor is None or not actor.is_authenticated:
        raise PermissionError("Login is required.")

    if not actor.has_role("Super Admin", "Admin", "Nurse", "Doctor", "Women’s Health Doctor"):
        raise PermissionError("Nursing view access is required.")


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


def _clean_optional(value):
    return value or None


def _validate_pain_score(value):
    if value is None:
        return
    if value < 0 or value > 10:
        raise NursingServiceError("pain_score must be between 0 and 10")


def _validate_spo2(value):
    if value is None:
        return
    if value < 0 or value > 100:
        raise NursingServiceError("oxygen_saturation must be between 0 and 100")


def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI from kg and cm.

    Returns None if weight or height is missing.
    """
    if weight_kg in (None, "") or height_cm in (None, ""):
        return None

    try:
        weight = Decimal(str(weight_kg))
        height = Decimal(str(height_cm)) / Decimal("100")
    except (InvalidOperation, ValueError):
        raise NursingServiceError("weight_kg and height_cm must be numeric")

    if weight <= 0 or height <= 0:
        return None

    return round(weight / (height * height), 2)


def record_vital_signs(*, actor, patient_id, medical_record_id=None, **values):
    """Record EMR vital signs through the Nursing module."""
    _require_nursing_write(actor)
    patient = _require_patient(patient_id)

    _validate_pain_score(values.get("pain_score"))
    _validate_spo2(values.get("oxygen_saturation"))

    medical_record = None
    if medical_record_id:
        medical_record = db.session.get(MedicalRecord, medical_record_id)
        if medical_record is None or medical_record.patient_id != patient.id:
            raise NursingServiceError("medical_record_id is invalid for this patient")

    vital = VitalSign(
        patient_id=patient.id,
        medical_record=medical_record,
        recorded_by_id=actor.id,
        recorded_at=_now(),
        temperature_c=values.get("temperature_c"),
        pulse_bpm=values.get("pulse_bpm"),
        respiratory_rate=values.get("respiratory_rate"),
        systolic_bp=values.get("systolic_bp"),
        diastolic_bp=values.get("diastolic_bp"),
        oxygen_saturation=values.get("oxygen_saturation"),
        weight_kg=values.get("weight_kg"),
        height_cm=values.get("height_cm"),
        pain_score=values.get("pain_score"),
    )
    db.session.add(vital)
    db.session.flush()

    _audit(
        "nursing.vitals_recorded",
        actor,
        "VitalSign",
        vital.id,
        {"patient_id": patient.id, "medical_record_id": medical_record_id},
    )

    db.session.commit()
    return vital


def _build_structured_note(**parts):
    labels = (
        ("Subjective", parts.get("subjective_note")),
        ("Objective", parts.get("objective_note")),
        ("Nursing assessment", parts.get("nursing_assessment")),
        ("Nursing intervention", parts.get("nursing_intervention")),
        ("Response to care", parts.get("response_to_care")),
        ("Follow-up recommendation", parts.get("follow_up_recommendation")),
    )

    lines = []
    for label, value in labels:
        if value:
            lines.append(f"{label}:\n{value.strip()}")

    return "\n\n".join(lines).strip()


def create_nursing_note(
    *,
    actor,
    patient_id,
    medical_record_id=None,
    note_type="progress",
    subjective_note=None,
    objective_note=None,
    nursing_assessment=None,
    nursing_intervention=None,
    response_to_care=None,
    follow_up_recommendation=None,
):
    """Create an EMR NursingNote using one structured text field."""
    _require_nursing_write(actor)

    if not actor.has_role("Super Admin", "Admin", "Nurse"):
        raise PermissionError("Only nurses or administrators can add nursing notes.")

    patient = _require_patient(patient_id)

    medical_record = None
    if medical_record_id:
        medical_record = db.session.get(MedicalRecord, medical_record_id)
        if medical_record is None or medical_record.patient_id != patient.id:
            raise NursingServiceError("medical_record_id is invalid for this patient")

    note = _build_structured_note(
        subjective_note=subjective_note,
        objective_note=objective_note,
        nursing_assessment=nursing_assessment,
        nursing_intervention=nursing_intervention,
        response_to_care=response_to_care,
        follow_up_recommendation=follow_up_recommendation,
    )

    if not note:
        raise NursingServiceError("At least one nursing note field is required")

    item = NursingNote(
        patient_id=patient.id,
        medical_record=medical_record,
        nurse_user_id=actor.id,
        note_type=note_type or "progress",
        note=note,
        recorded_at=_now(),
    )
    db.session.add(item)
    db.session.flush()

    _audit(
        "nursing.note_created",
        actor,
        "NursingNote",
        item.id,
        {"patient_id": patient.id, "medical_record_id": medical_record_id},
    )

    db.session.commit()
    return item


def create_care_plan(
    *,
    actor,
    patient_id,
    medical_record_id=None,
    nursing_diagnosis,
    goals,
    interventions,
    evaluation=None,
    status="active",
):
    _require_nursing_write(actor)

    if status not in {"active", "improved", "completed", "cancelled"}:
        raise NursingServiceError("care plan status is invalid")

    patient = _require_patient(patient_id)

    medical_record = None
    if medical_record_id:
        medical_record = db.session.get(MedicalRecord, medical_record_id)
        if medical_record is None or medical_record.patient_id != patient.id:
            raise NursingServiceError("medical_record_id is invalid for this patient")

    care_plan = NursingCarePlan(
        patient_id=patient.id,
        medical_record=medical_record,
        created_by_id=actor.id,
        nursing_diagnosis=nursing_diagnosis.strip(),
        goals=goals.strip(),
        interventions=interventions.strip(),
        evaluation=_clean_optional(evaluation),
        status=status,
    )
    db.session.add(care_plan)
    db.session.flush()

    _audit(
        "nursing.care_plan_created",
        actor,
        "NursingCarePlan",
        care_plan.id,
        {"patient_id": patient.id, "status": status},
    )

    db.session.commit()
    return care_plan


def administer_medication(
    *,
    actor,
    patient_id,
    medical_record_id=None,
    prescription_item_id=None,
    medication_name,
    dose=None,
    scheduled_time=None,
    given_at=None,
    status="given",
    missed_reason=None,
    patient_reaction=None,
    notes=None,
):
    _require_nursing_write(actor)

    if status not in {"given", "missed", "held", "refused"}:
        raise NursingServiceError("medication administration status is invalid")

    if status in {"missed", "held", "refused"} and not missed_reason:
        raise NursingServiceError("missed_reason is required when medication is not given")

    patient = _require_patient(patient_id)

    medical_record = None
    if medical_record_id:
        medical_record = db.session.get(MedicalRecord, medical_record_id)
        if medical_record is None or medical_record.patient_id != patient.id:
            raise NursingServiceError("medical_record_id is invalid for this patient")

    administration = MedicationAdministration(
        patient_id=patient.id,
        medical_record=medical_record,
        prescription_item_id=_clean_optional(prescription_item_id),
        medication_name=medication_name.strip(),
        dose=_clean_optional(dose),
        scheduled_time=scheduled_time,
        given_at=given_at or (_now() if status == "given" else None),
        status=status,
        given_by_id=actor.id,
        missed_reason=_clean_optional(missed_reason),
        patient_reaction=_clean_optional(patient_reaction),
        notes=_clean_optional(notes),
    )
    db.session.add(administration)
    db.session.flush()

    _audit(
        "nursing.medication_administered",
        actor,
        "MedicationAdministration",
        administration.id,
        {"patient_id": patient.id, "status": status},
    )

    db.session.commit()
    return administration


def get_assigned_patients(actor=None):
    """Simple assignment substitute.

    For now, nursing patients are today's arrived/booked appointment patients
    plus recent active patients. No separate assignment model.
    """
    if actor is not None:
        _require_nursing_view(actor)

    today = _now().date()

    appointment_patients = db.session.scalars(
        db.select(Patient)
        .join(Appointment)
        .where(
            Appointment.deleted_at.is_(None),
            db.func.date(Appointment.scheduled_start) == today,
            Appointment.status.in_(("booked", "arrived", "in_progress")),
            Patient.deleted_at.is_(None),
        )
        .order_by(Patient.last_name, Patient.first_name)
    ).all()

    if appointment_patients:
        return appointment_patients

    return db.session.scalars(
        db.select(Patient)
        .where(Patient.deleted_at.is_(None))
        .order_by(Patient.created_at.desc())
        .limit(20)
    ).all()


def get_today_nursing_tasks(actor=None):
    if actor is not None:
        _require_nursing_view(actor)

    today = _now().date()

    medication_tasks = db.session.scalars(
        db.select(MedicationAdministration)
        .where(
            MedicationAdministration.deleted_at.is_(None),
            db.func.date(MedicationAdministration.created_at) == today,
        )
        .order_by(MedicationAdministration.created_at.desc())
        .limit(10)
    ).all()

    active_care_plans = db.session.scalars(
        db.select(NursingCarePlan)
        .where(
            NursingCarePlan.deleted_at.is_(None),
            NursingCarePlan.status == "active",
        )
        .order_by(NursingCarePlan.created_at.desc())
        .limit(10)
    ).all()

    return {
        "medication_tasks": medication_tasks,
        "active_care_plans": active_care_plans,
    }


def build_simple_nursing_alerts(actor=None):
    if actor is not None:
        _require_nursing_view(actor)

    alerts = []

    recent_vitals = db.session.scalars(
        db.select(VitalSign)
        .where(VitalSign.deleted_at.is_(None))
        .order_by(VitalSign.recorded_at.desc())
        .limit(50)
    ).all()

    for vital in recent_vitals:
        patient = db.session.get(Patient, vital.patient_id)
        patient_name = (
            f"{patient.first_name} {patient.last_name}".strip()
            if patient
            else "Unknown patient"
        )

        if vital.oxygen_saturation is not None and vital.oxygen_saturation < 92:
            alerts.append(
                {
                    "severity": "critical",
                    "patient": patient_name,
                    "message": f"Low SpO2: {vital.oxygen_saturation}%",
                    "created_at": vital.recorded_at,
                }
            )

        if vital.temperature_c is not None and vital.temperature_c >= 38:
            alerts.append(
                {
                    "severity": "high",
                    "patient": patient_name,
                    "message": f"Fever: {vital.temperature_c} °C",
                    "created_at": vital.recorded_at,
                }
            )

        if vital.pain_score is not None and vital.pain_score >= 8:
            alerts.append(
                {
                    "severity": "high",
                    "patient": patient_name,
                    "message": f"High pain score: {vital.pain_score}/10",
                    "created_at": vital.recorded_at,
                }
            )

    missed_medications = db.session.scalars(
        db.select(MedicationAdministration)
        .where(
            MedicationAdministration.deleted_at.is_(None),
            MedicationAdministration.status.in_(("missed", "held", "refused")),
        )
        .order_by(MedicationAdministration.created_at.desc())
        .limit(20)
    ).all()

    for item in missed_medications:
        patient = db.session.get(Patient, item.patient_id)
        patient_name = (
            f"{patient.first_name} {patient.last_name}".strip()
            if patient
            else "Unknown patient"
        )
        alerts.append(
            {
                "severity": "moderate",
                "patient": patient_name,
                "message": f"{item.medication_name} was {item.status}",
                "created_at": item.created_at,
            }
        )

    return alerts[:20]


def build_nursing_dashboard(actor):
    _require_nursing_view(actor)

    recent_vitals = db.session.scalars(
        db.select(VitalSign)
        .where(VitalSign.deleted_at.is_(None))
        .order_by(VitalSign.recorded_at.desc())
        .limit(10)
    ).all()

    recent_notes = db.session.scalars(
        db.select(NursingNote)
        .where(NursingNote.deleted_at.is_(None))
        .order_by(NursingNote.recorded_at.desc())
        .limit(10)
    ).all()

    recent_medications = db.session.scalars(
        db.select(MedicationAdministration)
        .where(MedicationAdministration.deleted_at.is_(None))
        .order_by(MedicationAdministration.created_at.desc())
        .limit(10)
    ).all()

    active_care_plans = db.session.scalars(
        db.select(NursingCarePlan)
        .where(
            NursingCarePlan.deleted_at.is_(None),
            NursingCarePlan.status == "active",
        )
        .order_by(NursingCarePlan.created_at.desc())
        .limit(10)
    ).all()

    return {
        "assigned_patients": get_assigned_patients(actor),
        "today_tasks": get_today_nursing_tasks(actor),
        "recent_vitals": recent_vitals,
        "recent_notes": recent_notes,
        "recent_medications": recent_medications,
        "active_care_plans": active_care_plans,
        "alerts": build_simple_nursing_alerts(actor),
    }