"""Phase 11 Dentistry workflow tests."""
from datetime import date, datetime, timedelta
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from extensions import db
from models import (DentalChart, DentalImage, DentalProcedure, DentalRecord,
                    DentalSpecialty, Dentist, OrthodonticCase, Patient, Permission,
                    Role, User)
from services.dentistry import (add_dental_procedure, create_dental_record,
                                create_orthodontic_case, update_dental_chart,
                                update_orthodontic_progress, upload_dental_image)


@pytest.fixture()
def dentist_user(session):
    role = session.scalar(db.select(Role).where(Role.name == "Dentist")) or Role(name="Dentist")
    permission = session.scalar(db.select(Permission).where(Permission.code == "dentistry.manage")) or Permission(code="dentistry.manage", module="dentistry", action="manage")
    if permission not in role.permissions:
        role.permissions.append(permission)
    user = User(username="dentist1", email="dentist1@test.local", first_name="Dina", last_name="Dentist", roles=[role])
    user.set_password("test-password")
    session.add(user)
    session.commit()
    return user


@pytest.fixture()
def patient(session):
    patient = Patient(medical_record_number="MR-DEN-001", first_name="Mina", last_name="Patient", date_of_birth=date(1989, 1, 1), sex_at_birth="female")
    session.add(patient)
    session.commit()
    return patient


def create_dentist(session, user):
    specialty = session.scalar(db.select(DentalSpecialty).where(DentalSpecialty.code == "GEND")) or DentalSpecialty(code="GEND", name="General Dentistry")
    session.add(specialty)
    session.flush()
    dentist = Dentist(user_id=user.id, dental_specialty_id=specialty.id, license_number="DEN-100", qualifications=["DDS"])
    session.add(dentist)
    session.commit()
    return dentist


def test_dental_record_creation_and_chart_update(session, dentist_user, patient):
    dentist = create_dentist(session, dentist_user)
    record = create_dental_record(patient, actor=dentist_user, visit_at=datetime.now(), chief_complaint="Tooth pain", dental_history="None", oral_hygiene_history="Brushes twice daily", allergies=["Penicillin"], medical_alerts=["High blood pressure"], dental_diagnosis="Caries", treatment_plan="Fill and monitor")

    assert record.patient_id == patient.id
    assert record.dental_diagnosis == "Caries"

    updated = update_dental_chart(record, actor=dentist_user, tooth_number="18", condition="Caries", caries="moderate", missing_teeth=False, filled_teeth=True, crown_bridge=False, implant=False, root_canal=False, mobility="none", periodontal_notes="Healthy gingiva")

    chart = session.scalar(db.select(DentalChart).where(DentalChart.dental_record_id == record.id))
    assert updated is record
    assert chart.tooth_number == "18"
    assert chart.caries == "moderate"
    assert chart.periodontal_notes == "Healthy gingiva"


def test_dental_procedure_creation_and_orthodontic_case(session, dentist_user, patient):
    dentist = create_dentist(session, dentist_user)
    record = create_dental_record(patient, actor=dentist_user, visit_at=datetime.now(), chief_complaint="Broken tooth")
    procedure = add_dental_procedure(record, actor=dentist_user, procedure_name="Composite filling", tooth_number="21", diagnosis="Fracture", treatment_details="Shade matched", materials_used=["Resin"], dentist_notes="Completed", performed_at=datetime.now(), follow_up_date=date.today() + timedelta(days=14), cost_placeholder=120.0)
    assert procedure.procedure_name == "Composite filling"
    assert procedure.cost_placeholder == 120.0

    case = create_orthodontic_case(patient, actor=dentist_user, dental_record=record, diagnosis="Crowding", malocclusion_class="Class I", appliance_type="Clear aligner", treatment_plan="Monitor every 6 weeks", progress_notes="Initial fitting")
    assert case.diagnosis == "Crowding"
    updated = update_orthodontic_progress(case, actor=dentist_user, progress_notes="Progress noted", status="active")
    assert updated.progress_notes == "Progress noted"


def test_image_upload_validation(session, dentist_user, patient):
    create_dentist(session, dentist_user)
    record = create_dental_record(patient, actor=dentist_user, visit_at=datetime.now(), chief_complaint="Checkup")
    invalid = FileStorage(stream=BytesIO(b"not-an-image"), filename="bad.exe", content_type="application/octet-stream")
    with pytest.raises(ValueError):
        upload_dental_image(record, actor=dentist_user, file_storage=invalid, image_type="xray")

    valid = FileStorage(stream=BytesIO(b"fake-image-data"), filename="xray.png", content_type="image/png")
    image = upload_dental_image(record, actor=dentist_user, file_storage=valid, image_type="xray", tooth_number="11", description="Upper anterior")
    assert image.image_type == "xray"
    assert session.get(DentalImage, image.id) is not None


def test_unauthorized_user_cannot_edit_dentistry_records(client, session, dentist_user, patient):
    create_dentist(session, dentist_user)
    record = create_dental_record(patient, actor=dentist_user, visit_at=datetime.now(), chief_complaint="Checkup")
    receptionist = User(username="reception1", email="reception1@test.local", first_name="Rina", last_name="Reception", roles=[Role(name="Receptionist")])
    receptionist.set_password("test-password")
    session.add(receptionist)
    session.commit()

    client.post("/auth/login", data={"identifier": receptionist.username, "password": "test-password"})
    assert client.get(f"/dentistry/{record.id}/chart").status_code == 403
    assert client.get(f"/dentistry/{record.id}/procedures/create").status_code == 403
