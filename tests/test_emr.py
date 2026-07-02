from datetime import date, datetime, timezone

from models import Doctor, MedicalRecord, Patient, Specialty, User


def test_medical_record_links_patient_and_doctor(session):
    user = User(username="emrdoctor", email="emrdoctor@example.test", first_name="Omar", last_name="Hassan")
    user.set_password("test-password")
    doctor = Doctor(user=user, specialty=Specialty(code="CARD", name="Cardiology"), license_number="LIC-EMR")
    patient = Patient(medical_record_number="MRN-EMR", first_name="Lina", last_name="Yousef", date_of_birth=date(1985, 1, 1), sex_at_birth="female")
    record = MedicalRecord(record_number="REC-001", patient=patient, doctor=doctor, encounter_at=datetime.now(timezone.utc), chief_complaint="Review")
    session.add(record)
    session.commit()

    assert record in patient.medical_records
    assert record in doctor.medical_records
