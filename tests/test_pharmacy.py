"""Phase 9 pharmacy workflow tests."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from extensions import db
from models import (AuditLog, Doctor, Medication, MedicalRecord, Patient,
                    PatientMedicationHistory, Permission, Prescription,
                    PrescriptionItem, Role, Specialty, StockMovement, User)
from services.pharmacy_service import (PharmacyError, add_stock,
                                       complete_dispensing, create_medication,
                                       dispense_prescription_item,
                                       get_expired_items, get_low_stock_items,
                                       review_prescription,
                                       send_prescription_to_pharmacy)


def make_user(session, name, role_name, permissions=()):
    role = session.scalar(db.select(Role).where(Role.name == role_name)) or Role(name=role_name)
    for code in permissions:
        permission = session.scalar(db.select(Permission).where(Permission.code == code)) or Permission(
            code=code, module="pharmacy", action=code.split(".")[-1]
        )
        if permission not in role.permissions:
            role.permissions.append(permission)
    user = User(username=name, email=f"{name}@test.local", first_name=name.title(), last_name="Test", roles=[role])
    user.set_password("test-password")
    session.add(user)
    session.commit()
    return user


def context(session):
    admin = make_user(session, "pharmadmin", "Admin")
    doctor_user = make_user(session, "pharmdoctor", "Doctor")
    pharmacist = make_user(session, "pharmacist", "Pharmacist", ("pharmacy.dispense", "pharmacy.manage_inventory"))
    specialty = Specialty(code="PH9", name="Phase 9")
    doctor = Doctor(user=doctor_user, specialty=specialty, license_number="PH9-LIC")
    patient = Patient(medical_record_number="MR-PH9", first_name="Pharmacy", last_name="Patient", date_of_birth=date(1990, 1, 1), sex_at_birth="female")
    visit = MedicalRecord(record_number="VIS-PH9", patient=patient, doctor=doctor, encounter_type="outpatient", encounter_at=datetime.now(timezone.utc))
    session.add_all([specialty, doctor, patient, visit])
    session.commit()
    medication = create_medication(actor=admin, generic_name="Amoxicillin", brand_name="Amoxil", strength="500 mg", dosage_form="Capsule", route="Oral", category="Antibiotic", manufacturer="Example Pharma", barcode="PLACEHOLDER-1")
    prescription = Prescription(prescription_number="RX-PH9", patient=patient, doctor=doctor, medical_record=visit, prescribed_at=datetime.now(timezone.utc), status="created")
    item = PrescriptionItem(prescription=prescription, medication=medication, dose="500 mg", route="Oral", frequency="Three times daily", requested_quantity=Decimal("8"), dispensed_quantity=0)
    session.add_all([prescription, item])
    session.commit()
    return admin, doctor_user, pharmacist, patient, medication, prescription, item


def test_medication_creation_works(session):
    admin = make_user(session, "catalogadmin", "Admin")
    medication = create_medication(actor=admin, generic_name="Paracetamol", strength="500 mg", dosage_form="Tablet", is_active=True)
    assert medication.id and medication.form == "Tablet" and medication.is_active
    assert session.scalar(db.select(AuditLog).where(AuditLog.action == "pharmacy.medication_created"))


def test_prescription_appears_after_explicit_send_and_can_be_reviewed(session):
    _, doctor, pharmacist, _, _, prescription, _ = context(session)
    assert prescription.status == "created"
    send_prescription_to_pharmacy(prescription, actor=doctor)
    assert prescription.status == "sent_to_pharmacy" and prescription.sent_at
    review_prescription(prescription, actor=pharmacist, notes="Checked")
    assert prescription.status == "under_review" and prescription.pharmacy_notes == "Checked"


def test_dispensing_uses_fefo_reduces_stock_and_updates_history(session):
    _, doctor, pharmacist, patient, medication, prescription, item = context(session)
    later = add_stock(actor=pharmacist, medication=medication, batch_number="LATER", quantity=5, expiry_date=date.today() + timedelta(days=60), reorder_level=2)
    sooner = add_stock(actor=pharmacist, medication=medication, batch_number="SOONER", quantity=5, expiry_date=date.today() + timedelta(days=10), reorder_level=2)
    send_prescription_to_pharmacy(prescription, actor=doctor)
    review_prescription(prescription, actor=pharmacist)
    dispense_prescription_item(item, 8, actor=pharmacist, notes="Dispensed")
    assert sooner.quantity_on_hand == 0
    assert later.quantity_on_hand == 2
    assert prescription.status == "fully_dispensed"
    assert session.scalar(db.select(PatientMedicationHistory).where(PatientMedicationHistory.patient_id == patient.id)).quantity_dispensed == 8
    assert session.scalar(db.select(db.func.count(StockMovement.id))) == 4


def test_batch_override_and_partial_close(session):
    _, doctor, pharmacist, _, medication, prescription, item = context(session)
    first = add_stock(actor=pharmacist, medication=medication, batch_number="A", quantity=10, expiry_date=date.today() + timedelta(days=10))
    add_stock(actor=pharmacist, medication=medication, batch_number="B", quantity=10, expiry_date=date.today() + timedelta(days=20))
    send_prescription_to_pharmacy(prescription, actor=doctor)
    review_prescription(prescription, actor=pharmacist)
    dispense_prescription_item(item, 3, actor=pharmacist, inventory_batch=first)
    complete_dispensing(prescription, actor=pharmacist)
    assert prescription.status == "partially_dispensed" and prescription.completed_at
    with pytest.raises(PharmacyError):
        dispense_prescription_item(item, 1, actor=pharmacist)


def test_low_stock_and_expired_detection(session):
    _, _, pharmacist, _, medication, _, _ = context(session)
    low = add_stock(actor=pharmacist, medication=medication, batch_number="LOW", quantity=2, expiry_date=date.today() + timedelta(days=3), reorder_level=3)
    expired = add_stock(actor=pharmacist, medication=medication, batch_number="OLD", quantity=9, expiry_date=date.today() - timedelta(days=1), reorder_level=3)
    assert any(row["medication"].id == medication.id for row in get_low_stock_items())
    assert expired in get_expired_items() and low not in get_expired_items()


def test_expired_stock_cannot_be_dispensed(session):
    _, doctor, pharmacist, _, medication, prescription, item = context(session)
    expired = add_stock(actor=pharmacist, medication=medication, batch_number="EXPIRED", quantity=10, expiry_date=date.today() - timedelta(days=1))
    send_prescription_to_pharmacy(prescription, actor=doctor)
    review_prescription(prescription, actor=pharmacist)
    with pytest.raises(PharmacyError):
        dispense_prescription_item(item, 1, actor=pharmacist, inventory_batch=expired)


def test_unauthorized_user_cannot_dispense_route(client, session):
    _, doctor, pharmacist, _, medication, prescription, _ = context(session)
    add_stock(actor=pharmacist, medication=medication, batch_number="AUTH", quantity=10, expiry_date=date.today() + timedelta(days=10))
    send_prescription_to_pharmacy(prescription, actor=doctor)
    review_prescription(prescription, actor=pharmacist)
    receptionist = make_user(session, "pharmreception", "Receptionist")
    client.post("/auth/login", data={"identifier": receptionist.username, "password": "test-password"})
    assert client.get(f"/pharmacy/prescriptions/{prescription.id}/dispense").status_code == 403


def test_patient_can_only_view_own_medication_history(client, session):
    _, doctor, pharmacist, patient, medication, prescription, item = context(session)
    portal = make_user(session, "pharmpatient", "Patient")
    patient.user_id = portal.id
    add_stock(actor=pharmacist, medication=medication, batch_number="HISTORY", quantity=10, expiry_date=date.today() + timedelta(days=10))
    send_prescription_to_pharmacy(prescription, actor=doctor)
    review_prescription(prescription, actor=pharmacist)
    dispense_prescription_item(item, 2, actor=pharmacist)
    other = Patient(medical_record_number="MR-OTHER-PH9", first_name="Other", last_name="Patient", date_of_birth=date(1991, 1, 1), sex_at_birth="female")
    session.add(other)
    session.commit()
    client.post("/auth/login", data={"identifier": portal.username, "password": "test-password"})
    assert client.get(f"/patients/{patient.id}/medication-history").status_code == 200
    assert client.get(f"/patients/{other.id}/medication-history").status_code == 403
