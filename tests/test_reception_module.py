"""Phase 14 Reception module tests."""

from datetime import date, datetime, timedelta, timezone

from extensions import db
from models import (
    Appointment,
    BillingInitiation,
    Patient,
    Role,
    User,
)
from services.reception_service import (
    ReceptionServiceError,
    book_follow_up,
    check_in_patient,
    create_walk_in_visit,
    get_reception_dashboard,
    initiate_billing_placeholder,
    prevent_duplicate_patient,
    register_patient_from_reception,
    reorder_queue,
    search_patient_for_reception,
    update_queue_status,
)


def _role(session, name):
    role = session.execute(db.select(Role).filter_by(name=name)).scalar_one_or_none()
    if role is None:
        role = Role(name=name)
        session.add(role)
        session.flush()
    return role


def _user(session, suffix, role_name="Receptionist"):
    user = User(
        username=f"reception-{suffix}",
        email=f"reception-{suffix}@test.local",
        first_name="Reception",
        last_name="User",
    )
    user.set_password("test-password")
    user.roles.append(_role(session, role_name))
    session.add(user)
    session.commit()
    return user


def _patient(session, suffix="patient"):
    patient = Patient(
        medical_record_number=f"MR-RECEPTION-{suffix}",
        first_name="Reception",
        last_name="Patient",
        date_of_birth=date(1990, 1, 1),
        sex_at_birth="female",
        phone=f"0100000{suffix}"[:40],
    )
    session.add(patient)
    session.flush()
    return patient


def _appointment(session, patient, suffix="appointment", status="booked"):
    now = datetime.now(timezone.utc)
    scheduled_start = now.replace(hour=10, minute=0, second=0, microsecond=0)

    appointment = Appointment(
        appointment_number=f"APT-RECEPTION-{suffix}",
        patient_id=patient.id,
        scheduled_start=scheduled_start,
        appointment_type="consultation",
        status=status,
        reason="Test appointment",
    )
    session.add(appointment)
    session.commit()
    return appointment


def test_receptionist_can_register_patient(session):
    receptionist = _user(session, "register")

    patient = register_patient_from_reception(
        actor=receptionist,
        medical_record_number="MR-RECEPTION-REGISTERED",
        first_name="New",
        last_name="Patient",
        date_of_birth=date(1995, 5, 5),
        sex_at_birth="female",
        phone="01012345678",
        email="new.patient@test.local",
        address="Test address",
    )

    assert patient.id
    assert patient.medical_record_number == "MR-RECEPTION-REGISTERED"
    assert session.query(Patient).count() == 1


def test_duplicate_prevention_works(session):
    _patient(session, "duplicate")

    duplicate = prevent_duplicate_patient(
        first_name="Reception",
        last_name="Patient",
        phone="0100000duplicate"[:40],
        date_of_birth=date(1990, 1, 1),
    )

    assert duplicate is not None
    assert duplicate.medical_record_number == "MR-RECEPTION-duplicate"


def test_search_patient_for_reception(session):
    receptionist = _user(session, "search")
    patient = _patient(session, "search")

    results = search_patient_for_reception(
        actor=receptionist,
        query=patient.medical_record_number,
    )

    assert patient in results


def test_check_in_patient(session):
    receptionist = _user(session, "check-in")
    patient = _patient(session, "check-in")
    appointment = _appointment(session, patient, "check-in")

    checked_in = check_in_patient(
        actor=receptionist,
        appointment_id=appointment.id,
        reception_notes="Arrived early.",
    )

    assert checked_in.status == "arrived"
    assert checked_in.arrival_time is not None
    assert checked_in.queue_number is not None
    assert checked_in.reception_notes == "Arrived early."


def test_queue_status_update_and_reorder(session):
    receptionist = _user(session, "queue")
    patient = _patient(session, "queue")
    appointment = _appointment(session, patient, "queue")

    checked_in = check_in_patient(
        actor=receptionist,
        appointment_id=appointment.id,
    )

    waiting = update_queue_status(
        actor=receptionist,
        appointment_id=checked_in.id,
        status="waiting",
    )

    assert waiting.status == "waiting"

    moved = reorder_queue(
        actor=receptionist,
        appointment_id=waiting.id,
        queue_number=7,
    )

    assert moved.queue_number == 7


def test_walk_in_creation_works(session):
    receptionist = _user(session, "walk-in")

    appointment = create_walk_in_visit(
        actor=receptionist,
        medical_record_number="MR-RECEPTION-WALKIN",
        first_name="Walk",
        last_name="In",
        date_of_birth=date(1999, 9, 9),
        sex_at_birth="female",
        phone="01099999999",
        reason="Walk-in test",
        reception_notes="Urgent walk-in",
    )

    assert appointment.id
    assert appointment.appointment_type == "walk_in"
    assert appointment.status == "arrived"
    assert appointment.queue_number is not None
    assert appointment.patient.medical_record_number == "MR-RECEPTION-WALKIN"


def test_follow_up_booking_works(session):
    receptionist = _user(session, "follow-up")
    patient = _patient(session, "follow-up")
    original = _appointment(session, patient, "follow-up-original", status="completed")

    follow_up = book_follow_up(
        actor=receptionist,
        patient_id=patient.id,
        scheduled_start=datetime.now(timezone.utc) + timedelta(days=7),
        follow_up_of_id=original.id,
        reason="Follow-up test",
        notes="Reception booked follow-up.",
    )

    assert follow_up.id
    assert follow_up.appointment_type == "follow_up"
    assert follow_up.follow_up_of_id == original.id
    assert follow_up.patient_id == patient.id


def test_billing_initiation_placeholder_works(session):
    receptionist = _user(session, "billing")
    patient = _patient(session, "billing")
    appointment = _appointment(session, patient, "billing")

    billing = initiate_billing_placeholder(
        actor=receptionist,
        patient_id=patient.id,
        appointment_id=appointment.id,
        status="pending",
        notes="Initial billing placeholder.",
    )

    assert billing.id
    assert billing.status == "pending"
    assert billing.started_by_id == receptionist.id
    assert session.query(BillingInitiation).count() == 1


def test_receptionist_dashboard_access(session):
    receptionist = _user(session, "dashboard")
    patient = _patient(session, "dashboard")
    _appointment(session, patient, "dashboard")

    dashboard = get_reception_dashboard(receptionist)

    assert dashboard["counts"]["daily_appointments"] == 1
    assert len(dashboard["appointments"]) == 1


def test_unauthorized_user_cannot_access_reception_services(session):
    user = _user(session, "unauthorized", "Nurse")

    try:
        search_patient_for_reception(actor=user, query="test")
    except PermissionError as exc:
        assert "Reception access" in str(exc)
    else:
        raise AssertionError("Expected PermissionError")


def test_receptionist_cannot_register_duplicate_patient(session):
    receptionist = _user(session, "duplicate-register")
    _patient(session, "duplicate-register")

    try:
        register_patient_from_reception(
            actor=receptionist,
            medical_record_number="MR-RECEPTION-DUPLICATE-NEW",
            first_name="Reception",
            last_name="Patient",
            date_of_birth=date(1990, 1, 1),
            sex_at_birth="female",
            phone="0100000duplicate-register"[:40],
        )
    except ReceptionServiceError as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError("Expected ReceptionServiceError")