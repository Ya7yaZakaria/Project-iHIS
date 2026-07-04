"""Phase 8 radiology workflow tests."""

from datetime import date, datetime, timezone

from extensions import db
from models import (
    Doctor,
    ImagingStudy,
    MedicalRecord,
    Patient,
    Permission,
    RadiologyOrder,
    RadiologyReport,
    Role,
    Specialty,
    User,
)
from services.radiology_service import (
    create_imaging_study,
    create_radiology_report,
    mark_imaging_performed,
    mark_patient_arrived,
    review_radiology_report,
    schedule_radiology_order,
    verify_radiology_report,
)


def user(session, name, role_name, permission=None):
    role = session.scalar(db.select(Role).where(Role.name == role_name)) or Role(name=role_name)

    if permission:
        item = session.scalar(db.select(Permission).where(Permission.code == permission)) or Permission(
            code=permission,
            module="radiology",
            action="verify",
        )
        if item not in role.permissions:
            role.permissions.append(item)

    value = User(
        username=name,
        email=f"{name}@test.local",
        first_name=name.title(),
        last_name="Test",
        roles=[role],
    )
    value.set_password("test-password")

    session.add(value)
    session.commit()

    return value


def radiology_context(session):
    doctor_user = user(session, "raddoctor", "Doctor")
    radiology_user = user(session, "raduser", "Radiology", "radiology.verify")

    specialty = Specialty(
        code="RAD8",
        name="Radiology Phase 8",
    )

    doctor = Doctor(
        user=doctor_user,
        specialty=specialty,
        license_number="RAD8-LIC",
    )

    patient = Patient(
        medical_record_number="MR-RAD8",
        first_name="Rad",
        last_name="Patient",
        date_of_birth=date(1990, 1, 1),
        sex_at_birth="female",
    )

    visit = MedicalRecord(
        record_number="VIS-RAD8",
        patient=patient,
        doctor=doctor,
        encounter_type="outpatient",
        encounter_at=datetime.now(timezone.utc),
    )

    session.add_all([specialty, doctor, patient, visit])
    session.commit()

    return doctor_user, radiology_user, patient, visit


def test_catalog_creation(session):
    admin = user(session, "radadmin", "Admin")

    study = create_imaging_study(
        actor=admin,
        name="Pelvic Ultrasound",
        modality="Ultrasound",
        body_region="Pelvis",
        preparation_instructions="Full bladder",
        description="Standard pelvic ultrasound",
        is_active=True,
    )

    assert study.id
    assert study.name == "Pelvic Ultrasound"
    assert study.modality == "Ultrasound"
    assert session.scalar(db.select(ImagingStudy).where(ImagingStudy.name == "Pelvic Ultrasound"))


def test_complete_radiology_workflow(session):
    doctor_user, radiology_user, patient, visit = radiology_context(session)

    order = RadiologyOrder(
        order_number="RAD8-001",
        patient_id=patient.id,
        doctor_id=visit.doctor_id,
        medical_record_id=visit.id,
        modality="Ultrasound",
        body_part="Pelvis",
        priority="routine",
        status="requested",
        ordered_at=datetime.now(timezone.utc),
        clinical_indication="Pelvic pain",
    )
    session.add(order)
    session.commit()

    schedule_radiology_order(
        order,
        actor=radiology_user,
        scheduled_at=datetime.now(timezone.utc),
    )
    assert order.status == "scheduled"

    mark_patient_arrived(order, actor=radiology_user)
    assert order.status == "patient_arrived"

    mark_imaging_performed(order, actor=radiology_user)
    assert order.status == "imaging_performed"

    report = create_radiology_report(
        order,
        actor=radiology_user,
        radiologist_id=visit.doctor_id,
        clinical_indication="Pelvic pain",
        technique="Transabdominal ultrasound",
        findings="Normal uterus and ovaries.",
        impression="No acute pelvic abnormality.",
        recommendations="Clinical follow-up.",
        is_abnormal=False,
        is_critical=False,
    )

    assert report.status == "draft"
    assert order.status == "report_drafted"

    verify_radiology_report(report, actor=radiology_user)
    assert report.status == "verified"
    assert order.status == "report_verified"

    review_radiology_report(report, actor=doctor_user)
    assert report.status == "reviewed"
    assert order.status == "reviewed_by_doctor"


def test_patient_sees_only_verified_own_radiology_reports(client, session):
    doctor_user, radiology_user, patient, visit = radiology_context(session)

    portal = user(session, "radpatient", "Patient")
    patient.user_id = portal.id
    session.commit()

    order = RadiologyOrder(
        order_number="RAD8-002",
        patient_id=patient.id,
        doctor_id=visit.doctor_id,
        medical_record_id=visit.id,
        modality="MRI",
        body_part="Brain",
        priority="urgent",
        status="imaging_performed",
        ordered_at=datetime.now(timezone.utc),
        clinical_indication="Headache",
    )
    session.add(order)
    session.commit()

    report = create_radiology_report(
        order,
        actor=radiology_user,
        radiologist_id=visit.doctor_id,
        clinical_indication="Headache",
        technique="MRI brain",
        findings="No acute infarct.",
        impression="No acute intracranial abnormality.",
        recommendations=None,
        is_abnormal=False,
        is_critical=False,
    )

    client.post(
        "/auth/login",
        data={"identifier": portal.username, "password": "test-password"},
    )

    response = client.get(f"/patients/{patient.id}/radiology-reports")
    assert response.status_code == 200
    assert b"No acute intracranial abnormality" not in response.data

    client.get("/auth/logout")

    verify_radiology_report(report, actor=radiology_user)

    client.post(
        "/auth/login",
        data={"identifier": portal.username, "password": "test-password"},
    )

    response = client.get(f"/patients/{patient.id}/radiology-reports")
    assert response.status_code == 200
    assert b"No acute intracranial abnormality" in response.data


def test_unauthorized_user_cannot_verify_radiology_report_route(client, session):
    doctor_user, radiology_user, patient, visit = radiology_context(session)

    order = RadiologyOrder(
        order_number="RAD8-003",
        patient_id=patient.id,
        doctor_id=visit.doctor_id,
        medical_record_id=visit.id,
        modality="CT",
        body_part="Abdomen",
        priority="urgent",
        status="imaging_performed",
        ordered_at=datetime.now(timezone.utc),
        clinical_indication="Abdominal pain",
    )
    session.add(order)
    session.commit()

    report = create_radiology_report(
        order,
        actor=radiology_user,
        radiologist_id=visit.doctor_id,
        clinical_indication="Abdominal pain",
        technique="CT abdomen",
        findings="No free air.",
        impression="No acute surgical abdomen.",
        recommendations=None,
        is_abnormal=False,
        is_critical=False,
    )

    receptionist = user(session, "radreception", "Receptionist")

    client.post(
        "/auth/login",
        data={"identifier": receptionist.username, "password": "test-password"},
    )

    response = client.post(
        f"/radiology/orders/{order.id}/verify",
        data={"report_id": report.id},
    )

    assert response.status_code == 403