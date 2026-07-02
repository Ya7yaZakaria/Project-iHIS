from datetime import date, datetime, timedelta, timezone

from models import Appointment, Doctor, Patient, Specialty, User


def _provider(session):
    user = User(username="provider", email="provider@example.test", first_name="Mina", last_name="Salim")
    user.set_password("test-password")
    specialty = Specialty(code="IM", name="Internal Medicine", category="medical")
    doctor = Doctor(user=user, specialty=specialty, license_number="LIC-100")
    session.add_all([user, specialty, doctor])
    return doctor


def test_patient_doctor_and_appointment_creation(session):
    patient = Patient(medical_record_number="MRN-001", first_name="Nora", last_name="Ali", date_of_birth=date(1990, 5, 4), sex_at_birth="female")
    doctor = _provider(session)
    start = datetime.now(timezone.utc)
    appointment = Appointment(appointment_number="APT-001", patient=patient, doctor=doctor, scheduled_start=start, scheduled_end=start + timedelta(minutes=30))
    session.add(appointment)
    session.commit()

    assert appointment in patient.appointments
    assert appointment in doctor.appointments
    assert doctor.specialty.name == "Internal Medicine"
