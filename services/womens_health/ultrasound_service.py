import hashlib
from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename

from extensions import db
from models import (FetalBiometry, FetalDopplerRecord, WomensUltrasoundAttachment,
                    WomensUltrasoundReport)
from .common import audit, create_draft, now, require_manage, timeline_event


ALLOWED_FILES = {"pdf", "png", "jpg", "jpeg", "webp"}


def create_womens_ultrasound(profile, *, actor, scan_type, performed_at=None,
                             pregnancy=None, gynecology_journey=None,
                             infertility_journey=None, findings=None, impression=None,
                             measurements=None, placenta=None, liquor=None,
                             cervical_length_mm=None, pregnancy_visit_id=None,
                             antenatal_visit_id=None, gynecology_visit_id=None,
                             medical_record_id=None, radiology_order_id=None,
                             biometry=None, dopplers=None):
    require_manage(actor)
    report = WomensUltrasoundReport(report_number=f"WUS-{uuid4().hex[:10].upper()}",
        profile_id=profile.id, pregnancy=pregnancy, gynecology_journey_id=gynecology_journey.id if gynecology_journey else None,
        infertility_journey_id=infertility_journey.id if infertility_journey else None,
        medical_record_id=medical_record_id, pregnancy_visit_id=pregnancy_visit_id,
        antenatal_visit_id=antenatal_visit_id, gynecology_visit_id=gynecology_visit_id,
        radiology_order_id=radiology_order_id,
        performed_by_id=actor.doctor_profile.id if actor.doctor_profile else None,
        scan_type=scan_type, performed_at=performed_at or now(), findings=findings,
        impression=impression, measurements=measurements, placenta=placenta, liquor=liquor,
        cervical_length_mm=cervical_length_mm, status="draft")
    db.session.add(report); db.session.flush()
    for values in biometry or []: db.session.add(FetalBiometry(report=report, **values))
    for values in dopplers or []: db.session.add(FetalDopplerRecord(report=report, **values))
    create_draft(profile, report)
    timeline_event(profile, "ultrasound", f"{scan_type} ultrasound", report,
        event_at=report.performed_at, pregnancy=pregnancy, gynecology_journey=gynecology_journey,
        infertility_journey=infertility_journey, summary=impression)
    audit("womens_health.ultrasound_created", actor, report, scan_type=scan_type)
    db.session.commit(); return report


def attach_ultrasound_file(report, file_storage, *, actor, description=None):
    require_manage(actor)
    original = secure_filename(file_storage.filename or "")
    extension = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if extension not in ALLOWED_FILES: raise ValueError("Unsupported ultrasound attachment type.")
    data = file_storage.read()
    if not data or len(data) > current_app.config["MAX_CONTENT_LENGTH"]:
        raise ValueError("Attachment is empty or too large.")
    root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    folder = (root / "womens_health" / report.profile_id).resolve()
    if root not in folder.parents: raise ValueError("Unsafe attachment path.")
    folder.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid4().hex}.{extension}"; target = (folder / stored).resolve()
    if folder not in target.parents: raise ValueError("Unsafe attachment path.")
    target.write_bytes(data)
    attachment = WomensUltrasoundAttachment(report=report, uploaded_by_id=actor.id,
        original_name=original, stored_name=str(target.relative_to(root)),
        mime_type=file_storage.mimetype or "application/octet-stream", extension=extension,
        size_bytes=len(data), checksum_sha256=hashlib.sha256(data).hexdigest(), description=description)
    try:
        db.session.add(attachment); db.session.flush()
        audit("womens_health.ultrasound_attachment_added", actor, attachment, report_id=report.id)
        db.session.commit(); return attachment
    except Exception:
        db.session.rollback(); target.unlink(missing_ok=True); raise


def ultrasound_attachment_path(attachment):
    root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    path = (root / attachment.stored_name).resolve()
    if root not in path.parents or not path.is_file(): raise FileNotFoundError
    return path
