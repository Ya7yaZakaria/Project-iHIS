"""Phase 7 laboratory workflow tests."""

from datetime import date, datetime, timezone

import pytest

from extensions import db
from models import Doctor, LabOrder, LabResult, MedicalRecord, Patient, Permission, Role, Specialty, User
from services.laboratory_service import (collect_sample, create_lab_order, create_lab_test,
    enter_lab_result, review_lab_result, verify_lab_result)


def user(session, name, role_name, permission=None):
    role = session.scalar(db.select(Role).where(Role.name == role_name)) or Role(name=role_name)
    if permission:
        item = session.scalar(db.select(Permission).where(Permission.code == permission)) or Permission(code=permission, module="laboratory", action="validate")
        if item not in role.permissions: role.permissions.append(item)
    value = User(username=name, email=f"{name}@test.local", first_name=name.title(), last_name="Test", roles=[role]); value.set_password("test-password")
    session.add(value); session.commit(); return value


def clinical_context(session):
    doctor_user = user(session, "labdoctor", "Doctor"); lab_user = user(session, "labuser", "Laboratory", "laboratory.validate")
    specialty = Specialty(code="LAB7", name="Laboratory Phase 7")
    doctor = Doctor(user=doctor_user, specialty=specialty, license_number="LAB7-LIC")
    patient = Patient(medical_record_number="MR-LAB7", first_name="Lab", last_name="Patient", date_of_birth=date(1990, 1, 1), sex_at_birth="female")
    visit = MedicalRecord(record_number="VIS-LAB7", patient=patient, doctor=doctor, encounter_type="outpatient", encounter_at=datetime.now(timezone.utc))
    session.add_all([specialty, doctor, patient, visit]); session.commit(); return doctor_user, lab_user, patient, visit


def test_catalog_and_complete_result_workflow(session):
    doctor_user, lab_user, patient, visit = clinical_context(session)
    admin = user(session, "labadmin", "Admin")
    catalog = create_lab_test(actor=admin, code="CBC", name="Complete Blood Count", category="Hematology", unit="g/dL", reference_range="12-16", sample_type="Blood", turnaround_minutes=60, is_active=True)
    order = create_lab_order(visit, actor=doctor_user, lab_test=catalog)
    assert order.patient is patient and order.status == "requested"
    collect_sample(order, actor=lab_user); assert order.status == "sample_collected"
    result = enter_lab_result(order, actor=lab_user, component_name="Hemoglobin", result_type="numeric", value_numeric=11, unit="g/dL", reference_range="12-16", abnormal_flag="low")
    assert order.status == "result_entered" and result.abnormal_flag == "low"
    verify_lab_result(result, actor=lab_user); assert result.status == "verified"
    review_lab_result(result, actor=doctor_user); assert result.status == "reviewed" and order.status == "reviewed"


def test_unauthorized_user_cannot_review_or_verify_route(client, session):
    doctor_user, lab_user, _, visit = clinical_context(session)
    order = create_lab_order(visit, actor=doctor_user, test_name="Glucose")
    collect_sample(order, actor=lab_user)
    result = enter_lab_result(order, actor=lab_user, component_name="Glucose", result_type="numeric", value_numeric=100)
    receptionist = user(session, "labreception", "Receptionist")
    client.post("/auth/login", data={"identifier": receptionist.username, "password": "test-password"})
    assert client.post(f"/laboratory/orders/{order.id}/verify", data={"result_id": result.id}).status_code == 403


def test_patient_sees_only_verified_own_results(client, session):
    doctor_user, lab_user, patient, visit = clinical_context(session)
    portal = user(session, "labpatient", "Patient"); patient.user_id = portal.id; session.commit()
    order = create_lab_order(visit, actor=doctor_user, test_name="CRP"); collect_sample(order, actor=lab_user)
    result = enter_lab_result(order, actor=lab_user, component_name="CRP", result_type="text", value_text="Negative")
    client.post("/auth/login", data={"identifier": portal.username, "password": "test-password"})
    response = client.get(f"/patients/{patient.id}/lab-results"); assert response.status_code == 200 and b"CRP" not in response.data
    client.get("/auth/logout"); verify_lab_result(result, actor=lab_user)
    client.post("/auth/login", data={"identifier": portal.username, "password": "test-password"})
    response = client.get(f"/patients/{patient.id}/lab-results"); assert b"CRP" in response.data
