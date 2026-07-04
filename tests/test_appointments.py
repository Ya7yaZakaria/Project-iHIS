"""Phase 6 appointment and reception workflow tests."""

from datetime import date, datetime, timedelta, timezone

from extensions import db
from models import Appointment, AuditLog, Department, Doctor, Patient, Role, Specialty, User
from services import appointment_service


def user_with_role(session, username, role_name):
    role = session.execute(db.select(Role).filter_by(name=role_name)).scalar_one_or_none() or Role(name=role_name)
    user = User(username=username, email=f"{username}@example.test", first_name=username.title(), last_name="Tester", roles=[role])
    user.set_password("safe-test-password"); session.add(user); session.commit(); return user


def context(session):
    receptionist = user_with_role(session, "phase6reception", "Receptionist")
    doctor_user = user_with_role(session, "phase6doctor", "Doctor")
    specialty = Specialty(code="P6", name="Phase 6 Medicine")
    department = Department(code="P6D", name="Phase 6 Clinic")
    doctor = Doctor(user=doctor_user, specialty=specialty, department=department, license_number="P6-LIC")
    patient = Patient(medical_record_number="MRN-P6", first_name="Clinic", last_name="Patient", date_of_birth=date(1990, 1, 1), sex_at_birth="female", phone="01000000000")
    session.add_all([specialty, department, doctor, patient]); session.commit()
    return receptionist, doctor_user, doctor, patient


def test_create_update_cancel_and_audit(session):
    receptionist, _, doctor, patient = context(session)
    start = datetime.now(timezone.utc) + timedelta(days=1)
    appointment = appointment_service.create_appointment(patient_id=patient.id, doctor_id=doctor.id, scheduled_start=start, reason="Review", created_by=receptionist)
    appointment_service.update_appointment(appointment.id, reason="Updated review", updated_by=receptionist)
    appointment_service.cancel_appointment(appointment.id, reason="Patient request", cancelled_by=receptionist)
    assert appointment.status == "cancelled"
    assert {row.action for row in session.scalars(db.select(AuditLog)).all()} >= {"appointment.created", "appointment.updated", "appointment.cancelled"}


def test_reschedule_and_follow_up(session):
    receptionist, _, doctor, patient = context(session)
    start = datetime.now(timezone.utc) + timedelta(days=1)
    appointment = appointment_service.create_appointment(patient_id=patient.id, doctor_id=doctor.id, scheduled_start=start, created_by=receptionist)
    appointment_service.reschedule_appointment(appointment.id, scheduled_start=start + timedelta(days=1), rescheduled_by=receptionist)
    appointment.status = "completed"; session.commit()
    follow = appointment_service.schedule_follow_up(appointment.id, scheduled_start=start + timedelta(days=14), created_by=receptionist)
    assert follow.follow_up_of_id == appointment.id
    assert appointment.status == "follow_up_scheduled"


def test_check_in_queue_and_no_show(session):
    receptionist, _, doctor, patient = context(session)
    now = datetime.now(timezone.utc)
    first = appointment_service.create_appointment(patient_id=patient.id, doctor_id=doctor.id, scheduled_start=now, created_by=receptionist)
    second = appointment_service.create_appointment(patient_id=patient.id, doctor_id=doctor.id, scheduled_start=now + timedelta(minutes=30), created_by=receptionist)
    appointment_service.mark_arrived(first.id, marked_by=receptionist)
    appointment_service.mark_waiting(first.id, marked_by=receptionist)
    appointment_service.mark_no_show(second.id, marked_by=receptionist)
    assert appointment_service.get_waiting_queue()[0].id == first.id
    assert second.status == "no_show"


def test_doctor_consultation_creates_visit(session):
    receptionist, doctor_user, doctor, patient = context(session)
    appointment = appointment_service.create_appointment(patient_id=patient.id, doctor_id=doctor.id, scheduled_start=datetime.now(timezone.utc), created_by=receptionist)
    appointment_service.mark_arrived(appointment.id, marked_by=receptionist)
    appointment, visit = appointment_service.start_consultation(appointment.id, doctor_id=doctor.id, started_by=doctor_user)
    assert appointment.status == "in_consultation"
    assert visit.appointment_id == appointment.id
    appointment_service.complete_appointment(appointment.id, completed_by=doctor_user)
    assert appointment.status == "completed"


def test_duplicate_patient_detection(session):
    _, _, _, patient = context(session)
    duplicate = appointment_service.prevent_duplicate_patient(first_name="clinic", last_name="patient", phone=patient.phone, date_of_birth=patient.date_of_birth)
    assert duplicate.id == patient.id


def test_route_permissions_and_patient_ownership(client, session):
    receptionist, _, doctor, patient = context(session)
    portal = user_with_role(session, "phase6patient", "Patient"); patient.user_id = portal.id
    other = Patient(medical_record_number="MRN-P6-OTHER", first_name="Other", last_name="Patient", date_of_birth=date(1980, 1, 1), sex_at_birth="male")
    own = Appointment(appointment_number="APT-P6-OWN", patient=patient, doctor=doctor, scheduled_start=datetime.now(timezone.utc), status="booked")
    other_appointment = Appointment(appointment_number="APT-P6-OTHER", patient=other, doctor=doctor, scheduled_start=datetime.now(timezone.utc), status="booked")
    session.add_all([other, own, other_appointment]); session.commit()
    client.post("/auth/login", data={"identifier": portal.username, "password": "safe-test-password"})
    assert client.get(f"/appointments/{own.id}").status_code == 200
    assert client.get(f"/appointments/{other_appointment.id}").status_code == 403
    assert client.get("/appointments/create").status_code == 403


def test_reception_dashboard_today_and_check_in_routes(client, session):
    receptionist, _, doctor, patient = context(session)
    appointment = appointment_service.create_appointment(patient_id=patient.id, doctor_id=doctor.id,
        scheduled_start=datetime.now(timezone.utc), created_by=receptionist)
    client.post("/auth/login", data={"identifier": receptionist.username, "password": "safe-test-password"})
    assert client.get("/reception").status_code == 200
    assert client.get("/appointments/today").status_code == 200
    response = client.post("/reception/check-in", data={"appointment_id": appointment.id, "reception_notes": "Arrived"}, follow_redirects=True)
    session.refresh(appointment)
    assert response.status_code == 200
    assert appointment.status == "arrived"
    assert appointment.queue_number == 1
