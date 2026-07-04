"""Practical dentistry workflow services for the iHIS EMR."""
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename

from extensions import db
from models import DentalChart, DentalImage, DentalProcedure, DentalRecord, Dentist, OrthodonticCase
from services.auth_service import log_auth_event

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}


class DentalModuleError(ValueError):
    pass


def _now():
    return datetime.now(timezone.utc)


def _ensure_dentistry_access(actor):
    if actor is None:
        raise PermissionError("A user context is required.")
    if actor.has_role("Super Admin", "Admin", "Dentist"):
        return
    if actor.has_role("Doctor"):
        return
    raise PermissionError("You are not permitted to manage dentistry records.")


def _audit(action, actor, record=None, **details):
    payload = {"record_id": getattr(record, "id", None), **details}
    log_auth_event(action, actor=actor, details=payload)


def _dentist_for_actor(actor):
    if not actor:
        return None
    if hasattr(actor, "dentist_profile") and actor.dentist_profile:
        return actor.dentist_profile
    return db.session.scalar(db.select(Dentist).where(Dentist.user_id == actor.id))


def create_dental_record(patient, *, actor, visit_at, chief_complaint=None, dental_history=None, oral_hygiene_history=None,
                         allergies=None, medical_alerts=None, dental_complaints=None, dental_diagnosis=None,
                         treatment_plan=None, examination=None, status="active", dentist=None, medical_record=None):
    _ensure_dentistry_access(actor)
    dentist = dentist or _dentist_for_actor(actor)
    record = DentalRecord(
        patient_id=patient.id,
        dentist_id=(dentist.id if dentist else None),
        medical_record_id=(medical_record.id if medical_record else None),
        visit_at=visit_at,
        chief_complaint=chief_complaint,
        dental_history=dental_history,
        oral_hygiene_history=oral_hygiene_history,
        allergies=allergies or [],
        medical_alerts=medical_alerts or [],
        dental_complaints=dental_complaints,
        dental_diagnosis=dental_diagnosis,
        examination=examination,
        treatment_plan=treatment_plan,
        status=status,
    )
    db.session.add(record)
    db.session.flush()
    _audit("dentistry.record_created", actor, record, patient_id=patient.id)
    db.session.commit()
    return record


def update_dental_record(record, *, actor, **fields):
    _ensure_dentistry_access(actor)
    for key in ("chief_complaint", "dental_history", "oral_hygiene_history", "allergies", "medical_alerts",
                "dental_complaints", "dental_diagnosis", "examination", "treatment_plan", "status"):
        if key in fields:
            setattr(record, key, fields[key])
    _audit("dentistry.record_updated", actor, record)
    db.session.commit()
    return record


def update_dental_chart(record, *, actor, tooth_number, condition, caries=None, missing_teeth=None, filled_teeth=None,
                        crown_bridge=None, implant=None, root_canal=None, mobility=None, periodontal_notes=None,
                        numbering_system="FDI", surfaces=None, notes=None):
    _ensure_dentistry_access(actor)
    chart = db.session.scalar(
        db.select(DentalChart).where(
            DentalChart.dental_record_id == record.id,
            DentalChart.tooth_number == tooth_number,
            DentalChart.numbering_system == numbering_system,
        )
    )
    if chart is None:
        chart = DentalChart(dental_record_id=record.id, tooth_number=tooth_number, numbering_system=numbering_system)
        db.session.add(chart)
    chart.condition = condition
    chart.caries = caries
    chart.missing_teeth = bool(missing_teeth)
    chart.filled_teeth = bool(filled_teeth)
    chart.crown_bridge = bool(crown_bridge)
    chart.implant = bool(implant)
    chart.root_canal = bool(root_canal)
    chart.mobility = mobility
    chart.periodontal_notes = periodontal_notes
    chart.surfaces = surfaces or {}
    chart.notes = notes
    _audit("dentistry.chart_updated", actor, record, tooth_number=tooth_number)
    db.session.commit()
    return record


def add_dental_procedure(record, *, actor, procedure_name, tooth_number, diagnosis=None, treatment_details=None,
                         materials_used=None, dentist_notes=None, performed_at=None, follow_up_date=None,
                         cost_placeholder=None, status="planned"):
    _ensure_dentistry_access(actor)
    procedure = DentalProcedure(
        dental_record_id=record.id,
        dentist_id=record.dentist_id,
        tooth_number=tooth_number,
        procedure_name=procedure_name,
        diagnosis=diagnosis,
        treatment_details=treatment_details,
        materials_used=materials_used or [],
        dentist_notes=dentist_notes,
        performed_at=performed_at or _now(),
        follow_up_date=follow_up_date,
        cost_placeholder=cost_placeholder,
        status=status,
    )
    db.session.add(procedure)
    db.session.flush()
    _audit("dentistry.procedure_created", actor, record, procedure_id=procedure.id)
    db.session.commit()
    return procedure


def create_orthodontic_case(patient, *, actor, dental_record=None, diagnosis=None, malocclusion_class=None,
                            appliance_type=None, treatment_plan=None, progress_notes=None, follow_up_visits=None,
                            start_date=None, expected_end_date=None, status="planned"):
    _ensure_dentistry_access(actor)
    dentist = _dentist_for_actor(actor)
    case = OrthodonticCase(
        patient_id=patient.id,
        dental_record_id=(dental_record.id if dental_record else None),
        dentist_id=(dentist.id if dentist else None),
        diagnosis=diagnosis,
        malocclusion_class=malocclusion_class,
        appliance_type=appliance_type,
        treatment_plan=treatment_plan,
        progress_notes=progress_notes,
        follow_up_visits=follow_up_visits or [],
        start_date=start_date or date.today(),
        expected_end_date=expected_end_date,
        status=status,
    )
    db.session.add(case)
    db.session.flush()
    _audit("dentistry.orthodontic_case_created", actor, dental_record, case_id=case.id)
    db.session.commit()
    return case


def update_orthodontic_progress(case, *, actor, progress_notes=None, status=None):
    _ensure_dentistry_access(actor)
    if progress_notes is not None:
        case.progress_notes = progress_notes
    if status is not None:
        case.status = status
    _audit("dentistry.orthodontic_case_updated", actor, None, case_id=case.id)
    db.session.commit()
    return case


def upload_dental_image(record, *, actor, file_storage, image_type, tooth_number=None, description=None):
    _ensure_dentistry_access(actor)
    original_name = secure_filename(file_storage.filename or "")
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Only PNG, JPG, JPEG, GIF, and PDF dental images are allowed.")
    data = file_storage.read()
    if not data:
        raise ValueError("The uploaded file is empty.")
    upload_root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    folder = upload_root / "dentistry" / record.id
    folder.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}.{extension}"
    path = (folder / stored_name).resolve()
    if upload_root not in path.parents:
        raise ValueError("Invalid upload path.")
    path.write_bytes(data)
    image = DentalImage(
        dental_record_id=record.id,
        image_type=image_type,
        file_path=str(path.relative_to(upload_root)),
        tooth_number=tooth_number,
        captured_at=_now(),
        description=description,
    )
    db.session.add(image)
    db.session.flush()
    _audit("dentistry.image_uploaded", actor, record, image_id=image.id, image_type=image_type)
    db.session.commit()
    return image


def build_dental_timeline(record):
    events = []
    events.append({"kind": "record", "label": "Dental record created", "timestamp": record.visit_at})
    for chart in sorted(record.charts, key=lambda item: item.tooth_number):
        events.append({"kind": "chart", "label": f"Chart updated for tooth {chart.tooth_number}", "timestamp": chart.updated_at})
    for procedure in sorted(record.procedures, key=lambda item: item.performed_at or item.created_at):
        events.append({"kind": "procedure", "label": procedure.procedure_name, "timestamp": procedure.performed_at or procedure.created_at})
    for image in sorted(record.images, key=lambda item: item.captured_at or item.created_at):
        events.append({"kind": "image", "label": f"{image.image_type} uploaded", "timestamp": image.captured_at or image.created_at})
    return sorted(events, key=lambda item: item["timestamp"], reverse=True)


__all__ = [
    "DentalModuleError",
    "add_dental_procedure",
    "build_dental_timeline",
    "create_dental_record",
    "create_orthodontic_case",
    "update_dental_chart",
    "update_dental_record",
    "update_orthodontic_progress",
    "upload_dental_image",
]
