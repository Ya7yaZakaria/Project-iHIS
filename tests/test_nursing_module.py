"""Simple Nursing module tests."""

from datetime import date, datetime, timezone
from decimal import Decimal
from extensions import db
from models import (
    MedicalRecord,
    MedicationAdministration,
    NursingCarePlan,
    NursingNote,
    Patient,
    Role,
    User,
    VitalSign,
)
from services.nursing_service import (
    NursingServiceError,
    administer_medication,
    calculate_bmi,
    create_care_plan,
    create_nursing_note,
    record_vital_signs,
)


def _role(session, name):
    role = session.execute(db.select(Role).filter_by(name=name)).scalar_one_or_none()
    if role is None:
        role = Role(name=name)
        session.add(role)
        session.flush()
    return role


def _user(session, suffix, role_name="Nurse"):
    user = User(
        username=f"nursing-{suffix}",
        email=f"nursing-{suffix}@test.local",
        first_name="Nursing",
        last_name="User",
    )
    user.set_password("test-password")
    user.roles.append(_role(session, role_name))
    session.add(user)
    session.commit()
    return user


def _patient(session, suffix="patient"):
    patient = Patient(
        medical_record_number=f"MR-NURSING-{suffix}",
        first_name="Nursing",
        last_name="Patient",
        date_of_birth=date(1990, 1, 1),
        sex_at_birth="female",
    )
    session.add(patient)
    session.flush()
    return patient


def _visit(session, patient, suffix="visit"):
    visit = MedicalRecord(
        record_number=f"VIS-NURSING-{suffix}",
        patient=patient,
        encounter_type="outpatient",
        encounter_at=datetime.now(timezone.utc),
    )
    session.add(visit)
    session.flush()
    return visit


def test_calculate_bmi():
    assert calculate_bmi(70, 170) == Decimal("24.22")
    assert calculate_bmi(None, 170) is None
    assert calculate_bmi(70, None) is None
    assert calculate_bmi(70, 0) is None


def test_record_vital_signs(session):
    nurse = _user(session, "vitals")
    patient = _patient(session, "vitals")
    visit = _visit(session, patient, "vitals")

    vital = record_vital_signs(
        actor=nurse,
        patient_id=patient.id,
        medical_record_id=visit.id,
        systolic_bp=120,
        diastolic_bp=80,
        pulse_bpm=90,
        temperature_c=37.2,
        respiratory_rate=18,
        oxygen_saturation=98,
        weight_kg=70,
        height_cm=170,
        pain_score=3,
    )

    assert vital.id
    assert vital.patient_id == patient.id
    assert vital.medical_record_id == visit.id
    assert vital.recorded_by_id == nurse.id
    assert session.query(VitalSign).count() == 1


def test_create_nursing_note(session):
    nurse = _user(session, "note")
    patient = _patient(session, "note")
    visit = _visit(session, patient, "note")

    note = create_nursing_note(
        actor=nurse,
        patient_id=patient.id,
        medical_record_id=visit.id,
        note_type="progress",
        subjective_note="Patient reports mild pain.",
        objective_note="Stable vitals.",
        nursing_assessment="Comfortable.",
        nursing_intervention="Position changed and reassurance given.",
        response_to_care="Improved comfort.",
        follow_up_recommendation="Continue observation.",
    )

    assert note.id
    assert note.patient_id == patient.id
    assert note.medical_record_id == visit.id
    assert "Subjective" in note.note
    assert "Nursing intervention" in note.note
    assert session.query(NursingNote).count() == 1


def test_create_care_plan(session):
    nurse = _user(session, "care-plan")
    patient = _patient(session, "care-plan")
    visit = _visit(session, patient, "care-plan")

    plan = create_care_plan(
        actor=nurse,
        patient_id=patient.id,
        medical_record_id=visit.id,
        nursing_diagnosis="Acute pain related to procedure.",
        goals="Pain score below 3.",
        interventions="Monitor pain score and provide comfort measures.",
        evaluation="Initial plan.",
        status="active",
    )

    assert plan.id
    assert plan.patient_id == patient.id
    assert plan.status == "active"
    assert session.query(NursingCarePlan).count() == 1


def test_administer_medication_given(session):
    nurse = _user(session, "med-given")
    patient = _patient(session, "med-given")
    visit = _visit(session, patient, "med-given")

    item = administer_medication(
        actor=nurse,
        patient_id=patient.id,
        medical_record_id=visit.id,
        medication_name="Paracetamol",
        dose="1 g",
        status="given",
    )

    assert item.id
    assert item.status == "given"
    assert item.given_at is not None
    assert item.given_by_id == nurse.id
    assert session.query(MedicationAdministration).count() == 1


def test_missed_medication_requires_reason(session):
    nurse = _user(session, "med-missed")
    patient = _patient(session, "med-missed")

    try:
        administer_medication(
            actor=nurse,
            patient_id=patient.id,
            medication_name="Antibiotic",
            dose="1 vial",
            status="missed",
        )
    except NursingServiceError as exc:
        assert "missed_reason" in str(exc)
    else:
        raise AssertionError("Expected NursingServiceError")


def test_unauthorized_user_cannot_record_vitals(session):
    user = _user(session, "unauthorized", "Receptionist")
    patient = _patient(session, "unauthorized")

    try:
        record_vital_signs(
            actor=user,
            patient_id=patient.id,
            pulse_bpm=80,
        )
    except PermissionError as exc:
        assert "Nursing write access" in str(exc)
    else:
        raise AssertionError("Expected PermissionError")