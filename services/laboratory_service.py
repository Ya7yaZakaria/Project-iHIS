"""Laboratory catalog, specimen, result, and review workflows."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename

from extensions import db
from models import LabOrder, LabResult, LabTest, Notification
from services.auth_service import log_auth_event
from services.emr_service import create_lab_order as create_emr_lab_order

ORDER_OPEN = {"requested", "sample_collected", "in_progress", "result_entered"}
ALLOWED_FILES = {"pdf", "png", "jpg", "jpeg"}


class LaboratoryError(ValueError): pass
def _now(): return datetime.now(timezone.utc)
def _audit(action, actor, order, **details):
    log_auth_event(action, actor=actor, details={"lab_order_id": order.id, "patient_id": order.patient_id, **details})


def create_lab_order(visit, *, actor, lab_test=None, test_name=None, test_code=None, priority="routine", specimen_type=None, clinical_notes=None):
    if not lab_test and not test_name: raise LaboratoryError("A laboratory test is required.")
    order = create_emr_lab_order(visit, actor=actor, test_name=lab_test.name if lab_test else test_name,
        test_code=lab_test.code if lab_test else test_code, priority=priority,
        specimen_type=(lab_test.sample_type if lab_test else specimen_type), clinical_notes=clinical_notes)
    if lab_test: order.lab_test = lab_test
    _audit("laboratory.order_created", actor, order); db.session.commit(); return order


def update_lab_order(order, *, actor, **fields):
    if order.status != "requested": raise LaboratoryError("Only requested orders can be edited.")
    for key in ("priority", "department_id", "assigned_to_id", "clinical_notes"):
        if key in fields: setattr(order, key, fields[key] or None)
    _audit("laboratory.order_updated", actor, order); db.session.commit(); return order


def cancel_lab_order(order, *, actor, reason=None):
    if order.status not in ORDER_OPEN: raise LaboratoryError("This order can no longer be cancelled.")
    order.status = "cancelled"; order.cancelled_at = _now(); order.cancelled_by_id = actor.id; order.cancellation_reason = reason
    _audit("laboratory.order_cancelled", actor, order); db.session.commit(); return order


def collect_sample(order, *, actor):
    if order.status != "requested": raise LaboratoryError("Only requested orders can be collected.")
    order.status = "sample_collected"; order.collected_at = _now(); order.collected_by_id = actor.id
    _audit("laboratory.sample_collected", actor, order); db.session.commit(); return order


def start_processing(order, *, actor):
    if order.status != "sample_collected": raise LaboratoryError("Only collected samples can begin processing.")
    order.status = "in_progress"; order.processing_started_at = _now()
    _audit("laboratory.processing_started", actor, order); db.session.commit(); return order


def enter_lab_result(order, *, actor, component_name, result_type="text", value_numeric=None, value_text=None,
                     unit=None, reference_range=None, abnormal_flag="normal", comments=None):
    if order.status not in {"sample_collected", "in_progress", "result_entered"}: raise LaboratoryError("Collect the sample before entering results.")
    if result_type == "numeric" and value_numeric is None: raise LaboratoryError("A numeric result is required.")
    if result_type != "numeric" and not (value_text or "").strip(): raise LaboratoryError("A result value is required.")
    if order.status == "sample_collected": order.processing_started_at = _now()
    result = LabResult(order=order, component_name=component_name.strip(), result_type=result_type,
        value_numeric=value_numeric, value_text=(value_text or "").strip() or None, unit=(unit or "").strip() or None,
        reference_range=(reference_range or "").strip() or None, abnormal_flag=abnormal_flag,
        is_critical=abnormal_flag == "critical", comments=(comments or "").strip() or None,
        status="entered", resulted_at=_now(), entered_by_id=actor.id)
    order.status = "result_entered"; db.session.add(result); db.session.flush()
    _audit("laboratory.result_entered", actor, order, result_id=result.id, abnormal_flag=abnormal_flag); db.session.commit(); return result


def verify_lab_result(result, *, actor):
    if result.status != "entered": raise LaboratoryError("Only entered results can be verified.")
    result.status = "verified"; result.validated_by_id = actor.id; result.verified_at = _now()
    if all(item.status in {"verified", "reviewed"} for item in result.order.results): result.order.status = "verified"
    if result.is_critical and result.order.doctor and result.order.doctor.user_id:
        db.session.add(Notification(user_id=result.order.doctor.user_id, title="Critical laboratory result",
            message=f"Critical result for order {result.order.order_number} requires review.", category="laboratory",
            data={"lab_order_id": result.order.id}))
    _audit("laboratory.result_verified", actor, result.order, result_id=result.id, critical=result.is_critical); db.session.commit(); return result


def update_lab_result(result, *, actor, **fields):
    if result.status != "entered": raise LaboratoryError("Verified results cannot be modified.")
    if fields.get("result_type") == "numeric" and fields.get("value_numeric") is None: raise LaboratoryError("A numeric result is required.")
    for key in ("component_name", "result_type", "value_numeric", "value_text", "unit", "reference_range", "abnormal_flag", "comments"):
        if key in fields: setattr(result, key, fields[key])
    result.is_critical = result.abnormal_flag == "critical"; result.resulted_at = _now(); result.entered_by_id = actor.id
    _audit("laboratory.result_modified", actor, result.order, result_id=result.id, abnormal_flag=result.abnormal_flag); db.session.commit(); return result


def lab_attachment_path(result):
    if not result.attachment_stored_name: raise FileNotFoundError
    root = Path(current_app.config["UPLOAD_FOLDER"]).resolve(); path = (root / result.attachment_stored_name).resolve()
    if root not in path.parents or not path.is_file(): raise FileNotFoundError
    return path


def review_lab_result(result, *, actor):
    doctor = actor.doctor_profile
    if not doctor or result.order.doctor_id != doctor.id: raise PermissionError("Only the ordering Doctor may review this result.")
    if result.status != "verified": raise LaboratoryError("Only verified results can be reviewed.")
    result.status = "reviewed"; result.reviewed_by_id = doctor.id; result.reviewed_at = _now()
    if all(item.status == "reviewed" for item in result.order.results): result.order.status = "reviewed"
    _audit("laboratory.result_reviewed", actor, result.order, result_id=result.id); db.session.commit(); return result


def create_lab_test(*, actor, **fields):
    code = fields.pop("code").strip().upper()
    if db.session.execute(db.select(LabTest.id).where(LabTest.code == code)).first(): raise LaboratoryError("Laboratory test code already exists.")
    test = LabTest(code=code, **fields); db.session.add(test); db.session.flush()
    log_auth_event("laboratory.catalog_created", actor=actor, details={"lab_test_id": test.id}); db.session.commit(); return test


def update_lab_test(test, *, actor, **fields):
    code = fields.pop("code").strip().upper()
    if db.session.execute(db.select(LabTest.id).where(LabTest.code == code, LabTest.id != test.id)).first(): raise LaboratoryError("Laboratory test code already exists.")
    test.code = code
    for key, value in fields.items(): setattr(test, key, value)
    log_auth_event("laboratory.catalog_updated", actor=actor, details={"lab_test_id": test.id}); db.session.commit(); return test


def get_pending_lab_orders():
    return db.session.scalars(db.select(LabOrder).where(LabOrder.status.in_(ORDER_OPEN), LabOrder.deleted_at.is_(None)).order_by(LabOrder.ordered_at)).all()


def get_abnormal_results():
    return db.session.scalars(db.select(LabResult).where(LabResult.abnormal_flag.in_(["low", "high", "critical"]), LabResult.deleted_at.is_(None)).order_by(LabResult.resulted_at.desc())).all()


def attach_lab_file(result, file_storage, *, actor):
    original = secure_filename(file_storage.filename or ""); extension = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if extension not in ALLOWED_FILES: raise LaboratoryError("Only PDF, PNG, and JPEG attachments are allowed.")
    data = file_storage.read()
    if not data or len(data) > current_app.config["MAX_CONTENT_LENGTH"]: raise LaboratoryError("Attachment is empty or too large.")
    folder = Path(current_app.config["UPLOAD_FOLDER"]) / "laboratory" / result.order.patient_id; folder.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid4().hex}.{extension}"; path = (folder / stored).resolve()
    if folder.resolve() not in path.parents: raise LaboratoryError("Invalid attachment path.")
    path.write_bytes(data); result.attachment_name = original; result.attachment_stored_name = str(path.relative_to(Path(current_app.config["UPLOAD_FOLDER"]).resolve()))
    result.attachment_mime_type = file_storage.mimetype; result.attachment_size = len(data)
    _audit("laboratory.result_attachment_added", actor, result.order, result_id=result.id); db.session.commit(); return result
