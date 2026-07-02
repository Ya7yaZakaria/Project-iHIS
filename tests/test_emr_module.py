from datetime import date, datetime, timezone
from io import BytesIO

from werkzeug.datastructures import FileStorage

from extensions import db
from models import (Appointment, CareTeam, Doctor, Patient, Role, Specialty,
                    User)
from services.emr_service import (add_diagnosis, add_prescription_item,
                                  build_patient_timeline, create_lab_order,
                                  create_patient, create_prescription,
                                  create_radiology_order, create_visit,
                                  search_patients, upload_attachment)


def user_with_role(session, username, role_name):
    role=session.execute(db.select(Role).filter_by(name=role_name)).scalar_one_or_none() or Role(name=role_name)
    user=User(username=username,email=f"{username}@example.test",first_name=username.title(),last_name="Tester",roles=[role]); user.set_password("test-password")
    session.add(user); session.commit(); return user


def clinical_context(session):
    doctor_user=user_with_role(session,"doctor","Doctor")
    specialty=Specialty(code="EMR-T",name="EMR Test Specialty")
    doctor=Doctor(user=doctor_user,specialty=specialty,license_number="EMR-LIC")
    patient=Patient(medical_record_number="MRN-EMR-P5",first_name="EMR",last_name="Patient",date_of_birth=date(1990,1,1),sex_at_birth="female")
    appointment=Appointment(appointment_number="APT-EMR-P5",patient=patient,doctor=doctor,scheduled_start=datetime.now(timezone.utc))
    session.add_all([specialty,doctor,patient,appointment]); session.commit()
    return doctor_user,patient


def test_patient_creation_and_search(session):
    receptionist=user_with_role(session,"reception","Receptionist")
    patient=create_patient(actor=receptionist,first_name="Search",last_name="Patient",date_of_birth=date(2000,2,2),sex_at_birth="male")
    assert patient.medical_record_number.startswith("MRN-")
    assert search_patients("Search").items == [patient]


def test_visit_diagnosis_prescription_and_orders(session):
    doctor,patient=clinical_context(session)
    visit=create_visit(patient,actor=doctor,encounter_type="outpatient",chief_complaint="Headache",note_format="soap",subjective="Pain")
    diagnosis=add_diagnosis(visit,actor=doctor,description="Migraine",diagnosis_type="primary",icd10_code="G43")
    prescription=create_prescription(visit,actor=doctor,notes="Review in one week")
    item=add_prescription_item(prescription,actor=doctor,generic_name="Paracetamol",dose="500 mg",frequency="Twice daily",route="Oral",duration="5 days")
    lab=create_lab_order(visit,actor=doctor,test_name="CBC")
    radiology=create_radiology_order(visit,actor=doctor,modality="MRI",body_part="Brain")
    assert diagnosis.medical_record is visit
    assert item in prescription.items
    assert lab.status == radiology.status == "requested"
    kinds={event["kind"] for event in build_patient_timeline(patient)}
    assert {"visit","diagnosis","prescription","lab","radiology"}.issubset(kinds)


def test_attachment_validation_and_timeline(session,app,tmp_path):
    doctor,patient=clinical_context(session); app.config["UPLOAD_FOLDER"]=str(tmp_path)
    visit=create_visit(patient,actor=doctor,encounter_type="outpatient")
    valid=FileStorage(stream=BytesIO(b"%PDF-1.4 test"),filename="report.pdf",content_type="application/pdf")
    attachment=upload_attachment(patient,valid,actor=doctor,medical_record=visit)
    assert (tmp_path/attachment.stored_name).is_file()
    assert build_patient_timeline(patient)[0]["kind"] == "attachment"
    invalid=FileStorage(stream=BytesIO(b"MZ executable"),filename="bad.pdf",content_type="application/pdf")
    try:
        upload_attachment(patient,invalid,actor=doctor)
        assert False,"Expected validation failure"
    except ValueError:
        pass


def test_unrelated_doctor_cannot_access_patient(session):
    _,patient=clinical_context(session)
    unrelated=user_with_role(session,"unrelated","Doctor")
    unrelated.doctor_profile=Doctor(specialty=None,license_number="OTHER-LIC")
    session.add(unrelated); session.commit()
    try:
        create_visit(patient,actor=unrelated,encounter_type="outpatient")
        assert False,"Expected access denial"
    except PermissionError:
        pass


def test_patient_user_is_read_only(session):
    doctor,patient=clinical_context(session)
    portal=user_with_role(session,"portalpatient","Patient"); patient.user_id=portal.id; session.commit()
    try:
        create_visit(patient,actor=portal,encounter_type="outpatient")
        assert False,"Expected read-only denial"
    except PermissionError:
        pass
