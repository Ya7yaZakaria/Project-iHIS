"""Business services for the Rehabilitation module."""

from datetime import datetime, timezone

from extensions import db
from models import (
    ExerciseLibrary,
    RehabilitationAssessment,
    RehabilitationRecord,
    TherapyPlan,
    TherapySession,
)


class RehabilitationServiceError(ValueError):
    """Raised when rehabilitation business validation fails."""


def _now():
    return datetime.now(timezone.utc)


def _validate_required(value, field_name):
    if value in (None, ""):
        raise RehabilitationServiceError(f"{field_name} is required")


def _validate_pain_score(value, field_name):
    if value is None:
        return
    if value < 0 or value > 10:
        raise RehabilitationServiceError(f"{field_name} must be between 0 and 10")


def create_rehabilitation_record(**data):
    _validate_required(data.get("patient_id"), "patient_id")
    _validate_pain_score(data.get("pain_score"), "pain_score")

    data.setdefault("status", "active")

    record = RehabilitationRecord(**data)
    db.session.add(record)
    db.session.commit()
    return record


def update_rehabilitation_record(record, **data):
    if "pain_score" in data:
        _validate_pain_score(data.get("pain_score"), "pain_score")

    for key, value in data.items():
        setattr(record, key, value)

    db.session.commit()
    return record


def get_patient_rehabilitation_records(patient_id):
    _validate_required(patient_id, "patient_id")

    return (
        RehabilitationRecord.query
        .filter_by(patient_id=patient_id)
        .order_by(RehabilitationRecord.created_at.desc())
        .all()
    )


def get_rehabilitation_record(record_id):
    _validate_required(record_id, "record_id")
    return RehabilitationRecord.query.get(record_id)


def create_initial_assessment(**data):
    _validate_required(data.get("rehabilitation_record_id"), "rehabilitation_record_id")
    _validate_required(data.get("assessment_date"), "assessment_date")

    assessment = RehabilitationAssessment(**data)
    db.session.add(assessment)
    db.session.commit()
    return assessment


def update_initial_assessment(assessment, **data):
    for key, value in data.items():
        setattr(assessment, key, value)

    db.session.commit()
    return assessment


def create_therapy_plan(**data):
    _validate_required(data.get("rehabilitation_record_id"), "rehabilitation_record_id")
    _validate_required(data.get("patient_id"), "patient_id")
    _validate_required(data.get("therapist_id"), "therapist_id")
    _validate_required(data.get("start_date"), "start_date")
    _validate_required(data.get("goals"), "goals")

    data.setdefault("status", "active")
    data.setdefault("active", True)

    plan = TherapyPlan(**data)
    db.session.add(plan)
    db.session.commit()
    return plan


def update_therapy_plan(plan, **data):
    for key, value in data.items():
        setattr(plan, key, value)

    db.session.commit()
    return plan


def activate_therapy_plan(plan):
    plan.status = "active"
    plan.active = True
    db.session.commit()
    return plan


def deactivate_therapy_plan(plan):
    plan.status = "inactive"
    plan.active = False
    db.session.commit()
    return plan


def generate_home_program_summary(plan):
    lines = []

    if plan.exercise_program:
        lines.append(f"Exercise program: {plan.exercise_program}")
    if plan.home_program:
        lines.append(f"Home program: {plan.home_program}")
    if plan.frequency:
        lines.append(f"Frequency: {plan.frequency}")
    if plan.duration:
        lines.append(f"Duration: {plan.duration}")
    if plan.review_date:
        lines.append(f"Review date: {plan.review_date}")

    return "\n".join(lines)


def add_therapy_session(**data):
    _validate_required(data.get("therapy_plan_id"), "therapy_plan_id")
    _validate_required(data.get("patient_id"), "patient_id")
    _validate_required(data.get("therapist_id"), "therapist_id")
    _validate_required(data.get("scheduled_start"), "scheduled_start")

    _validate_pain_score(data.get("pain_before"), "pain_before")
    _validate_pain_score(data.get("pain_after"), "pain_after")

    data.setdefault("status", "scheduled")

    session = TherapySession(**data)
    db.session.add(session)
    db.session.commit()
    return session


def update_therapy_session(session, **data):
    if "pain_before" in data:
        _validate_pain_score(data.get("pain_before"), "pain_before")
    if "pain_after" in data:
        _validate_pain_score(data.get("pain_after"), "pain_after")

    for key, value in data.items():
        setattr(session, key, value)

    db.session.commit()
    return session


def complete_therapy_session(session, **data):
    if data:
        for key, value in data.items():
            setattr(session, key, value)

    _validate_pain_score(session.pain_before, "pain_before")
    _validate_pain_score(session.pain_after, "pain_after")

    session.status = "completed"
    if session.session_date is None:
        session.session_date = _now()

    db.session.commit()
    return session


def calculate_pain_change(session):
    if session.pain_before is None or session.pain_after is None:
        return None

    return session.pain_before - session.pain_after


def get_plan_sessions(plan_id):
    _validate_required(plan_id, "plan_id")

    return (
        TherapySession.query
        .filter_by(therapy_plan_id=plan_id)
        .order_by(TherapySession.scheduled_start.asc())
        .all()
    )


def create_exercise(**data):
    exercise_name = data.pop("exercise_name", None)

    if exercise_name and "name" not in data:
        data["name"] = exercise_name

    _validate_required(data.get("name"), "exercise_name")
    _validate_required(data.get("category"), "category")
    _validate_required(data.get("instructions"), "instructions")

    data.setdefault("active", True)

    exercise = ExerciseLibrary(**data)
    db.session.add(exercise)
    db.session.commit()
    return exercise


def update_exercise(exercise, **data):
    exercise_name = data.pop("exercise_name", None)

    if exercise_name and "name" not in data:
        data["name"] = exercise_name

    for key, value in data.items():
        setattr(exercise, key, value)

    db.session.commit()
    return exercise


def build_rehabilitation_progress(record):
    plans = list(record.therapy_plans or [])
    sessions = []

    for plan in plans:
        sessions.extend(plan.sessions or [])

    completed_sessions = [
        session for session in sessions
        if session.status == "completed"
    ]

    pain_after_values = [
        session.pain_after
        for session in completed_sessions
        if session.pain_after is not None
    ]

    latest_assessment = None
    if record.assessments:
        latest_assessment = sorted(
            record.assessments,
            key=lambda assessment: assessment.assessment_date,
            reverse=True,
        )[0]

    return {
        "record_id": record.id,
        "patient_id": record.patient_id,
        "status": record.status,
        "total_plans": len(plans),
        "active_plans": len([plan for plan in plans if plan.active]),
        "total_sessions": len(sessions),
        "completed_sessions": len(completed_sessions),
        "latest_pain_score": pain_after_values[-1] if pain_after_values else record.pain_score,
        "latest_functional_score": (
            latest_assessment.functional_score if latest_assessment else None
        ),
        "latest_assessment_id": latest_assessment.id if latest_assessment else None,
    }
def build_patient_rehabilitation_summary(patient):
    _validate_required(getattr(patient, "id", None), "patient_id")

    records = get_patient_rehabilitation_records(patient.id)

    if not records:
        return {
            "has_rehabilitation": False,
            "latest_record": None,
            "current_plan": None,
            "latest_assessment": None,
            "latest_session": None,
            "progress": None,
        }

    latest_record = records[0]

    current_plan = (
        TherapyPlan.query
        .filter_by(patient_id=patient.id, active=True)
        .order_by(TherapyPlan.start_date.desc(), TherapyPlan.created_at.desc())
        .first()
    )

    latest_assessment = (
        RehabilitationAssessment.query
        .join(RehabilitationRecord)
        .filter(RehabilitationRecord.patient_id == patient.id)
        .order_by(
            RehabilitationAssessment.assessment_date.desc(),
            RehabilitationAssessment.created_at.desc(),
        )
        .first()
    )

    latest_session = (
        TherapySession.query
        .filter_by(patient_id=patient.id)
        .order_by(
            TherapySession.scheduled_start.desc(),
            TherapySession.created_at.desc(),
        )
        .first()
    )

    return {
        "has_rehabilitation": True,
        "latest_record": latest_record,
        "current_plan": current_plan,
        "latest_assessment": latest_assessment,
        "latest_session": latest_session,
        "progress": build_rehabilitation_progress(latest_record),
    }