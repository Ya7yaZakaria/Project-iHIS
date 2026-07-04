"""Phase 12 Sprint 12.1 rehabilitation model tests."""

from datetime import date, datetime, timezone

from models import (
    ExerciseLibrary,
    MedicalRecord,
    Patient,
    PhysicalTherapist,
    RehabilitationAssessment,
    RehabilitationRecord,
    TherapyPlan,
    TherapySession,
    User,
)


def _patient(session, suffix):
    patient = Patient(
        medical_record_number=f"MR-REHAB-{suffix}",
        first_name="Rehab",
        last_name="Patient",
        date_of_birth=date(1985, 5, 12),
        sex_at_birth="female",
    )
    session.add(patient)
    session.flush()
    return patient


def _user(session, suffix):
    user = User(
        username=f"rehab-{suffix}",
        email=f"rehab-{suffix}@test.local",
        first_name="Rehab",
        last_name="Clinician",
    )
    user.set_password("test-password")
    session.add(user)
    session.flush()
    return user


def _record(session, suffix="record", with_links=True):
    patient = _patient(session, suffix)
    doctor = _user(session, f"doctor-{suffix}") if with_links else None
    visit = None
    if with_links:
        visit = MedicalRecord(
            record_number=f"VIS-REHAB-{suffix}",
            patient=patient,
            encounter_type="outpatient",
            encounter_at=datetime.now(timezone.utc),
        )
        session.add(visit)

    record = RehabilitationRecord(
        patient=patient,
        visit=visit,
        doctor=doctor,
        referral_source="Orthopedics",
        chief_complaint="Knee pain",
        functional_limitation="Difficulty climbing stairs",
        pain_score=6,
        mobility_status="Independent with pain",
        rehabilitation_diagnosis="Post-operative knee stiffness",
        therapy_goals="Restore painless mobility",
        status="active",
    )
    session.add(record)
    session.commit()
    return record


def _therapist(session, suffix):
    user = _user(session, f"pt-{suffix}")
    therapist = PhysicalTherapist(
        user=user,
        license_number=f"PT-{suffix}",
        specialty="Physical therapy",
    )
    session.add(therapist)
    session.flush()
    return therapist


def test_rehabilitation_record_creation(session):
    record = _record(session)

    assert record.id
    assert record.patient.medical_record_number == "MR-REHAB-record"
    assert record.visit.record_number == "VIS-REHAB-record"
    assert record.doctor.username == "rehab-doctor-record"
    assert record.created_at and record.updated_at


def test_rehabilitation_assessment_creation_and_relationship(session):
    record = _record(session, "assessment")
    assessment = RehabilitationAssessment(
        rehabilitation_record=record,
        assessment_date=date.today(),
        physical_exam="Mild swelling",
        range_of_motion="Flexion 100 degrees",
        muscle_power="Quadriceps 4/5",
        balance_assessment="Good static balance",
        gait_assessment="Mild antalgic gait",
        neurological_findings="Intact",
        red_flags="None",
        functional_score=72,
        assessment_summary="Improving after surgery",
    )
    session.add(assessment)
    session.commit()

    assert assessment in record.assessments
    assert assessment.rehabilitation_record is record


def test_therapy_plan_creation_and_relationship(session):
    record = _record(session, "plan")
    therapist = _therapist(session, "plan")
    plan = TherapyPlan(
        rehabilitation_record=record,
        patient_id=record.patient_id,
        therapist=therapist,
        plan_name="Knee mobility program",
        start_date=date.today(),
        goals="Improve flexion and strength",
        frequency="Three sessions weekly",
        duration="Six weeks",
        modalities="Heat and therapeutic exercise",
        exercise_program="Progressive strengthening",
        home_program="Daily range-of-motion exercises",
        review_date=date.today(),
        discharge_criteria="Independent home program",
        active=True,
    )
    session.add(plan)
    session.commit()

    assert plan in record.therapy_plans
    assert plan.rehabilitation_record is record
    assert plan.active


def test_therapy_session_creation_and_relationship(session):
    record = _record(session, "session")
    therapist = _therapist(session, "session")
    therapist_user = _user(session, "therapist-user-session")
    plan = TherapyPlan(rehabilitation_record=record, patient_id=record.patient_id, therapist=therapist, plan_name="Session plan", start_date=date.today(), goals=["Improve mobility"])
    therapy_session = TherapySession(
        therapy_plan=plan,
        patient_id=record.patient_id,
        therapist=therapist,
        therapist_user=therapist_user,
        scheduled_start=datetime.now(timezone.utc),
        session_date=datetime.now(timezone.utc),
        pain_before=5,
        pain_after=3,
        modalities_used="Heat",
        exercises_performed="Knee flexion and quadriceps sets",
        progress_notes="Range improved",
        patient_tolerance="Good",
        next_session_plan="Progress resistance",
    )
    session.add_all([plan, therapy_session])
    session.commit()

    assert therapy_session in plan.sessions
    assert therapy_session.therapy_plan is plan
    assert therapy_session.therapist_user is therapist_user


def test_exercise_library_creation(session):
    exercise = ExerciseLibrary(
        exercise_name="Supported knee flexion",
        category="Mobility",
        target_region="Knee",
        indication="Reduced knee flexion",
        contraindications="Acute unstable injury",
        instructions="Flex the knee within the comfortable range.",
        repetitions=10,
        sets=3,
        frequency="Twice daily",
        media_placeholder="knee-flexion-placeholder.png",
        active=True,
    )
    session.add(exercise)
    session.commit()

    assert exercise.id
    assert exercise.exercise_name == "Supported knee flexion"
    assert exercise.active


def test_nullable_visit_doctor_and_therapist_relationships(session):
    record = _record(session, "nullable", with_links=False)
    therapist = _therapist(session, "nullable")
    plan = TherapyPlan(rehabilitation_record=record, patient_id=record.patient_id, therapist=therapist, plan_name="Unassigned plan", start_date=date.today(), goals=["Maintain mobility"])
    therapy_session = TherapySession(
        therapy_plan=plan,
        patient_id=record.patient_id,
        therapist=therapist,
        scheduled_start=datetime.now(timezone.utc),
        session_date=datetime.now(timezone.utc),
    )
    session.add_all([plan, therapy_session])
    session.commit()

    assert record.visit is None
    assert record.doctor is None
    assert therapy_session.therapist_user is None
    assert therapy_session in plan.sessions

from services.rehabilitation_service import (
    RehabilitationServiceError,
    activate_therapy_plan,
    add_therapy_session,
    build_rehabilitation_progress,
    calculate_pain_change,
    complete_therapy_session,
    create_exercise,
    create_initial_assessment,
    create_rehabilitation_record,
    create_therapy_plan,
    deactivate_therapy_plan,
    generate_home_program_summary,
    update_exercise,
    update_rehabilitation_record,
)


def test_rehabilitation_service_create_and_update_record(session):
    patient = _patient(session, "service-record")

    record = create_rehabilitation_record(
        patient_id=patient.id,
        referral_source="Orthopedics",
        chief_complaint="Back pain",
        pain_score=7,
        mobility_status="Limited",
        rehabilitation_diagnosis="Mechanical low back pain",
        therapy_goals="Reduce pain",
    )

    assert record.id
    assert record.status == "active"

    updated = update_rehabilitation_record(record, pain_score=4, mobility_status="Improved")
    assert updated.pain_score == 4
    assert updated.mobility_status == "Improved"


def test_rehabilitation_service_rejects_invalid_pain_score(session):
    patient = _patient(session, "service-invalid-pain")

    try:
        create_rehabilitation_record(
            patient_id=patient.id,
            chief_complaint="Should fail",
            pain_score=11,
        )
    except RehabilitationServiceError as exc:
        assert "pain_score" in str(exc)
    else:
        raise AssertionError("Expected RehabilitationServiceError")


def test_rehabilitation_service_create_assessment(session):
    patient = _patient(session, "service-assessment")
    record = create_rehabilitation_record(patient_id=patient.id)

    assessment = create_initial_assessment(
        rehabilitation_record_id=record.id,
        assessment_date=date.today(),
        physical_exam="Tenderness",
        functional_score=60,
        assessment_summary="Initial rehab assessment",
    )

    assert assessment.id
    assert assessment.rehabilitation_record_id == record.id


def test_rehabilitation_service_therapy_plan_status_and_home_program(session):
    record = _record(session, "service-plan")
    therapist = _therapist(session, "service-plan")

    plan = create_therapy_plan(
        rehabilitation_record_id=record.id,
        patient_id=record.patient_id,
        therapist_id=therapist.id,
        plan_name="Back rehab",
        start_date=date.today(),
        goals=["Pain control"],
        frequency="3 times weekly",
        duration="4 weeks",
        exercise_program="Stretching",
        home_program="Daily walking",
        review_date=date.today(),
    )

    assert plan.id
    assert plan.active is True
    assert plan.status == "active"

    deactivate_therapy_plan(plan)
    assert plan.active is False
    assert plan.status == "inactive"

    activate_therapy_plan(plan)
    assert plan.active is True
    assert plan.status == "active"

    summary = generate_home_program_summary(plan)
    assert "Stretching" in summary
    assert "Daily walking" in summary
    assert "3 times weekly" in summary


def test_rehabilitation_service_session_completion_and_pain_change(session):
    record = _record(session, "service-session")
    therapist = _therapist(session, "service-session")

    plan = create_therapy_plan(
        rehabilitation_record_id=record.id,
        patient_id=record.patient_id,
        therapist_id=therapist.id,
        plan_name="Session plan",
        start_date=date.today(),
        goals=["Improve function"],
    )

    therapy_session = add_therapy_session(
        therapy_plan_id=plan.id,
        patient_id=record.patient_id,
        therapist_id=therapist.id,
        scheduled_start=datetime.now(timezone.utc),
        pain_before=8,
        pain_after=5,
        modalities_used="Heat",
    )

    assert therapy_session.status == "scheduled"
    assert calculate_pain_change(therapy_session) == 3

    completed = complete_therapy_session(
        therapy_session,
        progress_notes="Improved tolerance",
        patient_tolerance="Good",
    )

    assert completed.status == "completed"
    assert completed.session_date is not None


def test_rehabilitation_service_exercise_create_update(session):
    exercise = create_exercise(
        exercise_name="Wall squat",
        category="Strength",
        target_region="Knee",
        instructions="Perform slowly with support.",
        repetitions=10,
        sets=3,
        frequency="Daily",
    )

    assert exercise.id
    assert exercise.name == "Wall squat"

    updated = update_exercise(
        exercise,
        exercise_name="Supported wall squat",
        frequency="Twice daily",
    )

    assert updated.name == "Supported wall squat"
    assert updated.frequency == "Twice daily"


def test_rehabilitation_service_progress_summary(session):
    record = _record(session, "service-progress")
    therapist = _therapist(session, "service-progress")

    assessment = create_initial_assessment(
        rehabilitation_record_id=record.id,
        assessment_date=date.today(),
        functional_score=75,
        assessment_summary="Functional improvement",
    )

    plan = create_therapy_plan(
        rehabilitation_record_id=record.id,
        patient_id=record.patient_id,
        therapist_id=therapist.id,
        plan_name="Progress plan",
        start_date=date.today(),
        goals=["Improve walking"],
    )

    therapy_session = add_therapy_session(
        therapy_plan_id=plan.id,
        patient_id=record.patient_id,
        therapist_id=therapist.id,
        scheduled_start=datetime.now(timezone.utc),
        pain_before=6,
        pain_after=3,
    )
    complete_therapy_session(therapy_session)

    summary = build_rehabilitation_progress(record)

    assert assessment.id
    assert summary["record_id"] == record.id
    assert summary["total_plans"] == 1
    assert summary["active_plans"] == 1
    assert summary["total_sessions"] == 1
    assert summary["completed_sessions"] == 1
    assert summary["latest_pain_score"] == 3
    assert summary["latest_functional_score"] == 75