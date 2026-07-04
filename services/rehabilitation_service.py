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
    

def _validate_functional_score(value, field_name="functional_score"):
    if value is None:
        return

    if value < 0 or value > 100:
        raise RehabilitationServiceError(f"{field_name} must be between 0 and 100")


def _is_locked_status(status):
    return status in {"completed", "closed", "discharged"}


def _ensure_record_is_open(record, action="modify rehabilitation record"):
    if record is None:
        raise RehabilitationServiceError("rehabilitation_record_id is invalid")

    if _is_locked_status(record.status):
        raise RehabilitationServiceError(
            f"Cannot {action} when rehabilitation record is {record.status}"
        )


def _get_open_rehabilitation_record(record_id, action):
    _validate_required(record_id, "rehabilitation_record_id")

    record = db.session.get(RehabilitationRecord, record_id)
    _ensure_record_is_open(record, action)

    return record


def _get_therapy_plan(plan_id):
    _validate_required(plan_id, "therapy_plan_id")

    plan = db.session.get(TherapyPlan, plan_id)

    if plan is None:
        raise RehabilitationServiceError("therapy_plan_id is invalid")

    if plan.rehabilitation_record:
        _ensure_record_is_open(
            plan.rehabilitation_record,
            "add therapy session",
        )

    return plan


def _validate_plan_patient_matches_record(record, patient_id):
    _validate_required(patient_id, "patient_id")

    if record.patient_id != patient_id:
        raise RehabilitationServiceError(
            "patient_id must match the rehabilitation record patient"
        )


def _validate_session_patient_matches_plan(plan, patient_id):
    _validate_required(patient_id, "patient_id")

    if plan.patient_id != patient_id:
        raise RehabilitationServiceError(
            "patient_id must match the therapy plan patient"
        )
    

def create_rehabilitation_record(**data):
    _validate_required(data.get("patient_id"), "patient_id")
    _validate_pain_score(data.get("pain_score"), "pain_score")

    data.setdefault("status", "active")

    record = RehabilitationRecord(**data)
    db.session.add(record)
    db.session.commit()
    return record


def update_rehabilitation_record(record, **data):
    _ensure_record_is_open(record)

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
    return db.session.get(RehabilitationRecord, record_id)


def create_initial_assessment(**data):
    record = _get_open_rehabilitation_record(
        data.get("rehabilitation_record_id"),
        "create assessment",
    )

    _validate_required(data.get("assessment_date"), "assessment_date")
    _validate_functional_score(data.get("functional_score"))

    data["rehabilitation_record_id"] = record.id

    assessment = RehabilitationAssessment(**data)
    db.session.add(assessment)
    db.session.commit()
    return assessment


def update_initial_assessment(assessment, **data):
    if assessment.rehabilitation_record:
        _ensure_record_is_open(
            assessment.rehabilitation_record,
            "update assessment",
        )

    if "functional_score" in data:
        _validate_functional_score(data.get("functional_score"))

    for key, value in data.items():
        setattr(assessment, key, value)

    db.session.commit()
    return assessment


def create_therapy_plan(**data):
    record = _get_open_rehabilitation_record(
        data.get("rehabilitation_record_id"),
        "create therapy plan",
    )

    _validate_required(data.get("patient_id"), "patient_id")
    _validate_required(data.get("therapist_id"), "therapist_id")
    _validate_required(data.get("start_date"), "start_date")
    _validate_required(data.get("goals"), "goals")

    _validate_plan_patient_matches_record(record, data.get("patient_id"))

    data["rehabilitation_record_id"] = record.id
    data.setdefault("status", "active")
    data.setdefault("active", True)

    plan = TherapyPlan(**data)
    db.session.add(plan)
    db.session.commit()
    return plan


def update_therapy_plan(plan, **data):
    if plan.rehabilitation_record:
        _ensure_record_is_open(
            plan.rehabilitation_record,
            "update therapy plan",
        )

    if "patient_id" in data and plan.rehabilitation_record:
        _validate_plan_patient_matches_record(
            plan.rehabilitation_record,
            data.get("patient_id"),
        )

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
    plan = _get_therapy_plan(data.get("therapy_plan_id"))

    _validate_required(data.get("patient_id"), "patient_id")
    _validate_required(data.get("therapist_id"), "therapist_id")
    _validate_required(data.get("scheduled_start"), "scheduled_start")

    _validate_session_patient_matches_plan(plan, data.get("patient_id"))
    _validate_pain_score(data.get("pain_before"), "pain_before")
    _validate_pain_score(data.get("pain_after"), "pain_after")

    data["therapy_plan_id"] = plan.id
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


def _average(values):
    values = [value for value in values if value is not None]

    if not values:
        return None

    return round(
        sum(float(value) for value in values) / len(values),
        2,
    )


def _current_plan_for_record(record):
    active_plans = [
        plan
        for plan in (record.therapy_plans or [])
        if plan.active and not plan.is_deleted
    ]

    if not active_plans:
        return None

    return sorted(
        active_plans,
        key=lambda plan: (
            plan.start_date,
            plan.created_at,
        ),
        reverse=True,
    )[0]


def build_patient_progress_report():
    records = (
        RehabilitationRecord.query
        .filter(RehabilitationRecord.deleted_at.is_(None))
        .order_by(RehabilitationRecord.created_at.desc())
        .all()
    )

    rows = []

    for record in records:
        progress = build_rehabilitation_progress(record)
        current_plan = _current_plan_for_record(record)

        rows.append(
            {
                "record": record,
                "patient": record.patient,
                "diagnosis": record.rehabilitation_diagnosis,
                "current_plan": current_plan,
                "latest_pain_score": progress["latest_pain_score"],
                "latest_functional_score": progress["latest_functional_score"],
                "completed_sessions": progress["completed_sessions"],
                "progress": progress,
            }
        )

    return rows


def build_therapist_workload_report():
    workload = {}

    plans = (
        TherapyPlan.query
        .filter(TherapyPlan.deleted_at.is_(None))
        .all()
    )

    sessions = (
        TherapySession.query
        .filter(TherapySession.deleted_at.is_(None))
        .all()
    )

    def entry_for(therapist_id, therapist):
        key = therapist_id or "unassigned"

        if key not in workload:
            workload[key] = {
                "therapist": therapist,
                "active_plans": 0,
                "scheduled_sessions": 0,
                "completed_sessions": 0,
            }

        return workload[key]

    for plan in plans:
        entry = entry_for(plan.therapist_id, plan.therapist)

        if plan.active:
            entry["active_plans"] += 1

    for session in sessions:
        entry = entry_for(session.therapist_id, session.therapist)

        if session.status == "completed":
            entry["completed_sessions"] += 1
        elif session.status == "scheduled":
            entry["scheduled_sessions"] += 1

    return list(workload.values())


def build_rehabilitation_report_summary():
    records = (
        RehabilitationRecord.query
        .filter(RehabilitationRecord.deleted_at.is_(None))
        .all()
    )

    plans = (
        TherapyPlan.query
        .filter(TherapyPlan.deleted_at.is_(None))
        .all()
    )

    sessions = (
        TherapySession.query
        .filter(TherapySession.deleted_at.is_(None))
        .all()
    )

    patient_progress = build_patient_progress_report()
    therapist_workload = build_therapist_workload_report()

    latest_pain_scores = [
        row["latest_pain_score"]
        for row in patient_progress
    ]

    latest_functional_scores = [
        row["latest_functional_score"]
        for row in patient_progress
    ]

    records_needing_review = [
        row
        for row in patient_progress
        if row["record"].status == "active"
        and row["current_plan"] is None
    ]

    return {
        "record_count": len(records),
        "active_record_count": len(
            [record for record in records if record.status == "active"]
        ),
        "completed_record_count": len(
            [record for record in records if record.status == "completed"]
        ),
        "active_plan_count": len(
            [plan for plan in plans if plan.active]
        ),
        "total_session_count": len(sessions),
        "completed_session_count": len(
            [session for session in sessions if session.status == "completed"]
        ),
        "average_latest_pain_score": _average(latest_pain_scores),
        "average_latest_functional_score": _average(latest_functional_scores),
        "records_needing_review": records_needing_review,
        "patient_progress": patient_progress,
        "therapist_workload": therapist_workload,
    }