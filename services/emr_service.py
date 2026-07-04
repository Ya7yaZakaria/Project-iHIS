"""Central EMR workflows, access policy, timeline, and secure uploads."""

import hashlib
from decimal import Decimal
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import current_app
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload
from werkzeug.utils import secure_filename

from extensions import db
from models import (Appointment, CareTeam, Diagnosis, Doctor, LabOrder,
                    MedicalAttachment, MedicalRecord, Medication, NursingNote,
                    Patient, Prescription, PrescriptionItem, RadiologyOrder,
                    VitalSign, WomensHealthApproval, WomensHealthTimelineEvent)
from services.auth_service import log_auth_event


ALLOWED_UPLOADS = {"pdf", "png", "jpg", "jpeg", "doc", "docx", "txt"}
SIGNATURES = {"pdf": b"%PDF", "png": b"\x89PNG", "jpg": b"\xff\xd8\xff", "jpeg": b"\xff\xd8\xff", "docx": b"PK"}
CLINICAL_ROLES = {"Doctor", "Women’s Health Doctor"}


def _now(): return datetime.now(timezone.utc)
def _number(prefix): return f"{prefix}-{_now():%Y%m%d}-{uuid4().hex[:8].upper()}"


def generate_mrn():
    while True:
        value = _number("MRN")
        if not db.session.execute(db.select(Patient.id).filter_by(medical_record_number=value)).first(): return value


def _audit(action, actor, patient=None, resource_id=None, details=None):
    return log_auth_event(action, actor=actor, target_user=None, details={"patient_id": patient.id if patient else None, "resource_id": resource_id, **(details or {})})


def can_view_demographics(user, patient):
    return bool(user.has_role("Super Admin", "Admin", "Receptionist") or (user.has_role("Patient") and patient.user_id == user.id) or can_view_emr(user, patient, audit_denied=False))


def can_view_emr(user, patient, audit_denied=True):
    allowed = False
    if user.has_role("Super Admin"):
        allowed = True
    elif user.has_role("Patient"):
        allowed = patient.user_id == user.id
    elif user.has_role(*CLINICAL_ROLES) and user.doctor_profile:
        doctor_id = user.doctor_profile.id
        allowed = bool(db.session.execute(db.select(Appointment.id).where(Appointment.patient_id == patient.id, Appointment.doctor_id == doctor_id)).first() or db.session.execute(db.select(MedicalRecord.id).where(MedicalRecord.patient_id == patient.id, MedicalRecord.doctor_id == doctor_id)).first())
    if not allowed and user.has_role("Nurse", *CLINICAL_ROLES):
        allowed = bool(db.session.execute(db.select(CareTeam.id).where(CareTeam.patient_id == patient.id, CareTeam.members.any(id=user.id))).first())
    if not allowed and audit_denied:
        _audit("emr.access_denied", user, patient, details={"roles": [r.name for r in user.roles]}); db.session.commit()
    return allowed


def require_demographic_access(user, patient):
    if not can_view_demographics(user, patient): raise PermissionError("You cannot access this patient.")


def require_emr_access(user, patient, write=False):
    if not can_view_emr(user, patient): raise PermissionError("You cannot access this EMR.")
    if write and user.has_role("Patient"): raise PermissionError("Patient portal access is read-only.")


def _doctor_for(user):
    profile = user.doctor_profile
    if not profile or not profile.is_active: raise PermissionError("An active Doctor profile is required.")
    return profile


def create_patient(*, actor, first_name, last_name, date_of_birth, sex_at_birth, medical_record_number=None, **fields):
    if not actor.has_role("Super Admin", "Admin", "Receptionist"): raise PermissionError("Demographic registration access is required.")
    mrn = (medical_record_number or "").strip().upper() or generate_mrn()
    if db.session.execute(db.select(Patient.id).filter_by(medical_record_number=mrn)).first(): raise ValueError("Medical-record number already exists.")
    patient = Patient(medical_record_number=mrn, first_name=first_name.strip(), last_name=last_name.strip(), date_of_birth=date_of_birth, sex_at_birth=sex_at_birth, **fields)
    db.session.add(patient); db.session.flush()
    _audit("emr.patient_created", actor, patient, details={"mrn_override": bool(medical_record_number)})
    db.session.commit(); return patient


def update_patient(patient, *, actor, medical_record_number=None, **fields):
    if not actor.has_role("Super Admin", "Admin", "Receptionist"): raise PermissionError("Demographic update access is required.")
    old_mrn = patient.medical_record_number
    new_mrn = (medical_record_number or old_mrn).strip().upper()
    duplicate = db.session.execute(db.select(Patient.id).where(Patient.medical_record_number == new_mrn, Patient.id != patient.id)).first()
    if duplicate: raise ValueError("Medical-record number already exists.")
    patient.medical_record_number = new_mrn
    for key, value in fields.items(): setattr(patient, key, value)
    _audit("emr.patient_updated", actor, patient, details={"mrn_changed": old_mrn != new_mrn})
    db.session.commit(); return patient


def search_patients(search=None, page=1, per_page=20):
    stmt = db.select(Patient).where(Patient.deleted_at.is_(None))
    if search:
        pattern=f"%{search.strip()}%"
        stmt=stmt.where(or_(Patient.medical_record_number.ilike(pattern), Patient.first_name.ilike(pattern), Patient.last_name.ilike(pattern), Patient.phone.ilike(pattern), Patient.email.ilike(pattern)))
    return db.paginate(stmt.order_by(Patient.last_name, Patient.first_name), page=max(page,1), per_page=per_page, error_out=False)


def create_visit(patient, *, actor, encounter_type, encounter_at=None, appointment_id=None, **fields):
    require_emr_access(actor, patient, write=True); doctor=_doctor_for(actor)
    visit=MedicalRecord(record_number=_number("VIS"), patient=patient, doctor=doctor, appointment_id=appointment_id or None, encounter_type=encounter_type, encounter_at=encounter_at or _now(), **fields)
    db.session.add(visit); db.session.flush(); _audit("emr.visit_created", actor, patient, visit.id); db.session.commit(); return visit


def update_visit(visit, *, actor, **fields):
    require_emr_access(actor, visit.patient, write=True)
    if visit.doctor.user_id != actor.id and not actor.has_role("Super Admin"): raise PermissionError("Only the author may edit this visit.")
    for key,value in fields.items(): setattr(visit,key,value)
    _audit("emr.visit_updated",actor,visit.patient,visit.id); db.session.commit(); return visit


def add_diagnosis(visit, *, actor, description, diagnosis_type="secondary", icd10_code=None, notes=None):
    require_emr_access(actor,visit.patient,write=True); doctor=_doctor_for(actor)
    if diagnosis_type == "primary":
        for item in visit.diagnoses:
            if item.diagnosis_type == "primary" and not item.is_deleted: item.diagnosis_type="secondary"
    diagnosis=Diagnosis(medical_record=visit,patient_id=visit.patient_id,doctor_id=doctor.id,description=description.strip(),diagnosis_type=diagnosis_type,icd10_code=(icd10_code or "").strip() or None,diagnosed_at=_now())
    if notes: diagnosis.description=f"{diagnosis.description} — {notes.strip()}"
    db.session.add(diagnosis); db.session.flush(); _audit("emr.diagnosis_added",actor,visit.patient,diagnosis.id); db.session.commit(); return diagnosis


def create_prescription(visit, *, actor, notes=None):
    require_emr_access(actor,visit.patient,write=True); doctor=_doctor_for(actor)
    prescription=Prescription(prescription_number=_number("RX"),patient_id=visit.patient_id,doctor_id=doctor.id,medical_record=visit,prescribed_at=_now(),status="created",notes=notes)
    db.session.add(prescription); db.session.flush(); _audit("emr.prescription_created",actor,visit.patient,prescription.id); return prescription


def add_prescription_item(prescription, *, actor, generic_name, dose, frequency, route=None, duration=None, quantity=None, instructions=None, brand_name=None, strength=None):
    require_emr_access(actor,prescription.patient,write=True)
    medication=db.session.execute(db.select(Medication).where(db.func.lower(Medication.generic_name)==generic_name.strip().lower(), Medication.strength==(strength.strip() if strength else None))).scalar_one_or_none()
    if not medication:
        medication=Medication(generic_name=generic_name.strip(),brand_name=(brand_name or "").strip() or None,strength=(strength or "").strip() or None,route=(route or "").strip() or None)
        db.session.add(medication); db.session.flush()
    requested_quantity=Decimal(str(quantity or 1))
    if requested_quantity <= 0: raise ValueError("Prescription quantity must be greater than zero.")
    item=PrescriptionItem(prescription=prescription,medication=medication,dose=dose.strip(),route=(route or "").strip() or None,frequency=frequency.strip(),duration=(duration or "").strip() or None,quantity=str(requested_quantity),requested_quantity=requested_quantity,dispensed_quantity=0,instructions=(instructions or "").strip() or None)
    db.session.add(item); db.session.flush(); _audit("emr.prescription_item_added",actor,prescription.patient,item.id); db.session.commit(); return item


def create_lab_order(visit, *, actor, test_name, test_code=None, priority="routine", specimen_type=None, clinical_notes=None):
    require_emr_access(actor,visit.patient,write=True); doctor=_doctor_for(actor)
    order=LabOrder(order_number=_number("LAB"),patient=visit.patient,doctor_id=doctor.id,medical_record=visit,test_name=test_name.strip(),test_code=(test_code or "").strip() or None,priority=priority,status="requested",ordered_at=_now(),specimen_type=specimen_type,clinical_notes=clinical_notes)
    db.session.add(order); db.session.flush(); _audit("emr.lab_order_created",actor,visit.patient,order.id); db.session.commit(); return order


def create_radiology_order(visit, *, actor, modality, body_part, priority="routine", clinical_indication=None):
    require_emr_access(actor,visit.patient,write=True); doctor=_doctor_for(actor)
    order=RadiologyOrder(order_number=_number("RAD"),patient=visit.patient,doctor_id=doctor.id,medical_record_id=visit.id,modality=modality,body_part=body_part,priority=priority,status="requested",ordered_at=_now(),clinical_indication=clinical_indication)
    db.session.add(order); db.session.flush(); _audit("emr.radiology_order_created",actor,visit.patient,order.id); db.session.commit(); return order


def add_vital_sign(visit, *, actor, **values):
    require_emr_access(actor,visit.patient,write=True)
    if not actor.has_role("Nurse",*CLINICAL_ROLES): raise PermissionError("Clinical staff access required.")
    item=VitalSign(patient_id=visit.patient_id,medical_record=visit,recorded_by_id=actor.id,recorded_at=_now(),**values)
    db.session.add(item); db.session.flush(); _audit("emr.vitals_added",actor,visit.patient,item.id); db.session.commit(); return item


def add_nursing_note(visit, *, actor, note, note_type="progress"):
    require_emr_access(actor,visit.patient,write=True)
    if not actor.has_role("Nurse"): raise PermissionError("Nurse access required.")
    item=NursingNote(patient_id=visit.patient_id,medical_record=visit,nurse_user_id=actor.id,note=note.strip(),note_type=note_type,recorded_at=_now())
    db.session.add(item); db.session.flush(); _audit("emr.nursing_note_added",actor,visit.patient,item.id); db.session.commit(); return item


def upload_attachment(patient, file_storage, *, actor, medical_record=None, category="clinical_document", description=None):
    require_emr_access(actor,patient,write=True)
    original=secure_filename(file_storage.filename or "")
    if not original or "." not in original: raise ValueError("A valid filename is required.")
    extension=original.rsplit(".",1)[1].lower()
    if extension not in ALLOWED_UPLOADS: raise ValueError("File type is not allowed.")
    content=file_storage.stream.read(current_app.config["MAX_CONTENT_LENGTH"]+1)
    if not content: raise ValueError("Uploaded file is empty.")
    if len(content)>current_app.config["MAX_CONTENT_LENGTH"]: raise ValueError("Uploaded file is too large.")
    signature=SIGNATURES.get(extension)
    if signature and not content.startswith(signature): raise ValueError("File content does not match its extension.")
    patient_dir=(Path(current_app.config["UPLOAD_FOLDER"]).resolve()/"emr"/patient.id).resolve()
    root=Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    if root not in patient_dir.parents: raise ValueError("Unsafe upload path.")
    patient_dir.mkdir(parents=True,exist_ok=True)
    stored=f"{uuid4().hex}.{extension}"; target=(patient_dir/stored).resolve()
    if patient_dir not in target.parents: raise ValueError("Unsafe upload path.")
    target.write_bytes(content)
    attachment=MedicalAttachment(patient=patient,medical_record=medical_record,uploaded_by_id=actor.id,original_name=original,stored_name=f"emr/{patient.id}/{stored}",mime_type=file_storage.mimetype or mimetypes.guess_type(original)[0] or "application/octet-stream",extension=extension,size_bytes=len(content),checksum_sha256=hashlib.sha256(content).hexdigest(),category=category,description=description)
    try:
        db.session.add(attachment); db.session.flush(); _audit("emr.attachment_uploaded",actor,patient,attachment.id); db.session.commit(); return attachment
    except Exception:
        target.unlink(missing_ok=True); db.session.rollback(); raise


def attachment_path(attachment):
    root=Path(current_app.config["UPLOAD_FOLDER"]).resolve(); path=(root/attachment.stored_name).resolve()
    if root not in path.parents or not path.is_file(): raise FileNotFoundError("Attachment file is unavailable.")
    return path


def build_patient_timeline(patient, signed_womens_health_only=False):
    events=[]
    def add(at,kind,title,obj,url=None):
        if at: events.append({"at":at,"kind":kind,"title":title,"object":obj,"url":url})
    for v in patient.medical_records:
        add(v.encounter_at,"visit",f"{v.encounter_type.title()} visit",v)
        if v.follow_up_date: add(datetime.combine(v.follow_up_date,datetime.min.time(),tzinfo=timezone.utc),"follow_up","Scheduled follow-up",v)
        for d in v.diagnoses: add(d.diagnosed_at,"diagnosis",d.description,d)
    for p in patient.prescriptions: add(p.prescribed_at,"prescription",f"Prescription {p.prescription_number}",p)
    for o in patient.lab_orders:
        add(o.ordered_at,"lab",f"Lab ordered: {o.test_name}",o)
        for result in o.results:
            if result.status == "reviewed": add(result.reviewed_at or result.resulted_at,"lab_result",f"Lab result: {result.component_name}",result)
    for o in patient.radiology_orders: add(o.ordered_at,"radiology",f"{o.modality}: {o.body_part}",o)
    for a in patient.attachments: add(a.created_at,"attachment",a.original_name,a)
    if patient.womens_health_profile:
        wh_events = db.session.scalars(db.select(WomensHealthTimelineEvent).where(
            WomensHealthTimelineEvent.profile_id == patient.womens_health_profile.id,
            WomensHealthTimelineEvent.deleted_at.is_(None),
        )).all()
        if signed_womens_health_only:
            signed = {(x.source_type, x.source_id) for x in db.session.scalars(db.select(WomensHealthApproval).where(
                WomensHealthApproval.profile_id == patient.womens_health_profile.id,
                WomensHealthApproval.status == "signed",
            )).all()}
            wh_events = [event for event in wh_events if (event.source_type, event.source_id) in signed]
        for event in wh_events: add(event.event_at,"womens_health",event.title,event)
    return sorted(events,key=lambda event:event["at"],reverse=True)
