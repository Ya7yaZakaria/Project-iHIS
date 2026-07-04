"""Radiology catalog, order, imaging, report, attachment, and review workflows."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename

from extensions import db
from models import ImagingStudy, Notification, RadiologyAttachment, RadiologyOrder, RadiologyReport
from services.auth_service import log_auth_event
from services.emr_service import create_radiology_order as create_emr_radiology_order


ORDER_OPEN = {
    "requested",
    "scheduled",
    "patient_arrived",
    "imaging_performed",
    "report_drafted",
}

ALLOWED_FILES = {"pdf", "png", "jpg", "jpeg", "txt", "doc", "docx"}


class RadiologyError(ValueError):
    pass


def _now():
    return datetime.now(timezone.utc)


def _audit(action, actor, order, **details):
    log_auth_event(
        action,
        actor=actor,
        details={
            "radiology_order_id": order.id,
            "patient_id": order.patient_id,
            **details,
        },
    )


def create_imaging_study(*, actor, **fields):
    name = fields.pop("name").strip()
    if db.session.execute(db.select(ImagingStudy.id).where(ImagingStudy.name == name)).first():
        raise RadiologyError("Imaging study already exists.")

    study = ImagingStudy(name=name, **fields)
    db.session.add(study)
    db.session.flush()

    log_auth_event(
        "radiology.catalog_created",
        actor=actor,
        details={"imaging_study_id": study.id},
    )
    db.session.commit()
    return study


def update_imaging_study(study, *, actor, **fields):
    name = fields.pop("name").strip()
    if db.session.execute(
        db.select(ImagingStudy.id).where(
            ImagingStudy.name == name,
            ImagingStudy.id != study.id,
        )
    ).first():
        raise RadiologyError("Imaging study already exists.")

    study.name = name
    for key, value in fields.items():
        setattr(study, key, value)

    log_auth_event(
        "radiology.catalog_updated",
        actor=actor,
        details={"imaging_study_id": study.id},
    )
    db.session.commit()
    return study


def create_radiology_order(
    visit,
    *,
    actor,
    imaging_study=None,
    modality=None,
    body_part=None,
    priority="routine",
    clinical_indication=None,
):
    if imaging_study:
        modality = imaging_study.modality
        body_part = imaging_study.body_region

    if not modality or not body_part:
        raise RadiologyError("Modality and body region are required.")

    order = create_emr_radiology_order(
        visit,
        actor=actor,
        modality=modality,
        body_part=body_part,
        priority=priority,
        clinical_indication=clinical_indication,
    )

    if imaging_study:
        order.imaging_study = imaging_study

    _audit("radiology.order_created", actor, order)
    db.session.commit()
    return order


def update_radiology_order(order, *, actor, **fields):
    if order.status != "requested":
        raise RadiologyError("Only requested radiology orders can be edited.")

    for key in (
        "imaging_study_id",
        "assigned_radiology_user_id",
        "modality",
        "body_part",
        "priority",
        "clinical_indication",
    ):
        if key in fields:
            setattr(order, key, fields[key] or None)

    _audit("radiology.order_updated", actor, order)
    db.session.commit()
    return order


def cancel_radiology_order(order, *, actor, reason=None):
    if order.status not in ORDER_OPEN:
        raise RadiologyError("This order can no longer be cancelled.")

    order.status = "cancelled"
    order.cancelled_at = _now()
    order.cancellation_reason = reason

    _audit("radiology.order_cancelled", actor, order, reason=reason)
    db.session.commit()
    return order


def schedule_radiology_order(order, *, actor, scheduled_at, assigned_radiology_user_id=None):
    if order.status != "requested":
        raise RadiologyError("Only requested orders can be scheduled.")

    order.status = "scheduled"
    order.scheduled_at = scheduled_at
    order.assigned_radiology_user_id = assigned_radiology_user_id or order.assigned_radiology_user_id

    _audit("radiology.order_scheduled", actor, order, scheduled_at=scheduled_at.isoformat())
    db.session.commit()
    return order


def mark_patient_arrived(order, *, actor):
    if order.status != "scheduled":
        raise RadiologyError("Only scheduled orders can be marked as patient arrived.")

    order.status = "patient_arrived"
    order.patient_arrived_at = _now()

    _audit("radiology.patient_arrived", actor, order)
    db.session.commit()
    return order


def mark_imaging_performed(order, *, actor):
    if order.status not in {"scheduled", "patient_arrived"}:
        raise RadiologyError("Only scheduled or arrived patients can be marked performed.")

    order.status = "imaging_performed"
    order.imaging_performed_at = _now()

    _audit("radiology.imaging_performed", actor, order)
    db.session.commit()
    return order


def create_radiology_report(
    order,
    *,
    actor,
    radiologist_id=None,
    clinical_indication=None,
    technique=None,
    findings=None,
    impression=None,
    recommendations=None,
    is_abnormal=False,
    is_critical=False,
):
    if order.status not in {"imaging_performed", "report_drafted"}:
        raise RadiologyError("Imaging must be performed before report creation.")

    report = order.reports[0] if order.reports else RadiologyReport(order=order)

    report.radiologist_id = radiologist_id
    report.clinical_indication = clinical_indication
    report.technique = technique
    report.findings = findings
    report.impression = impression
    report.recommendations = recommendations
    report.is_abnormal = bool(is_abnormal)
    report.is_critical = bool(is_critical)
    report.status = "draft"
    report.reported_at = _now()

    order.status = "report_drafted"
    order.urgent_finding_flag = bool(is_critical)

    db.session.add(report)
    db.session.flush()

    if report.is_critical and order.doctor and order.doctor.user_id:
        db.session.add(
            Notification(
                user_id=order.doctor.user_id,
                title="Urgent radiology finding",
                message=f"Urgent finding for radiology order {order.order_number} requires review.",
                category="radiology",
                data={"radiology_order_id": order.id, "radiology_report_id": report.id},
            )
        )

    _audit(
        "radiology.report_created",
        actor,
        order,
        report_id=report.id,
        critical=report.is_critical,
    )
    db.session.commit()
    return report


def verify_radiology_report(report, *, actor):
    if report.status != "draft":
        raise RadiologyError("Only drafted reports can be verified.")

    report.status = "verified"
    report.verified_by_id = actor.id
    report.verified_at = _now()
    report.order.status = "report_verified"

    _audit("radiology.report_verified", actor, report.order, report_id=report.id)
    db.session.commit()
    return report


def review_radiology_report(report, *, actor):
    doctor = actor.doctor_profile
    if not doctor or report.order.doctor_id != doctor.id:
        raise PermissionError("Only the ordering Doctor may review this report.")

    if report.status != "verified":
        raise RadiologyError("Only verified reports can be reviewed.")

    report.status = "reviewed"
    report.reviewed_by_doctor_id = doctor.id
    report.reviewed_at = _now()
    report.order.status = "reviewed_by_doctor"

    _audit("radiology.report_reviewed", actor, report.order, report_id=report.id)
    db.session.commit()
    return report


def attach_radiology_file(order, file_storage, *, actor, category="image_or_report", description=None):
    original = secure_filename(file_storage.filename or "")
    extension = original.rsplit(".", 1)[-1].lower() if "." in original else ""

    if extension not in ALLOWED_FILES:
        raise RadiologyError("Unsupported radiology attachment type.")

    data = file_storage.read()
    if not data or len(data) > current_app.config["MAX_CONTENT_LENGTH"]:
        raise RadiologyError("Attachment is empty or too large.")

    folder = Path(current_app.config["UPLOAD_FOLDER"]) / "radiology" / order.patient_id
    folder.mkdir(parents=True, exist_ok=True)

    stored = f"{uuid4().hex}.{extension}"
    path = (folder / stored).resolve()

    if folder.resolve() not in path.parents:
        raise RadiologyError("Invalid attachment path.")

    path.write_bytes(data)

    attachment = RadiologyAttachment(
        order=order,
        uploaded_by_id=actor.id,
        original_name=original,
        stored_name=str(path.relative_to(Path(current_app.config["UPLOAD_FOLDER"]).resolve())),
        mime_type=file_storage.mimetype,
        extension=extension,
        size_bytes=len(data),
        checksum_sha256="pending",
        category=category,
        description=description,
    )

    db.session.add(attachment)
    db.session.flush()

    _audit(
        "radiology.file_attached",
        actor,
        order,
        attachment_id=attachment.id,
        category=category,
    )
    db.session.commit()
    return attachment


def radiology_attachment_path(attachment):
    root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    path = (root / attachment.stored_name).resolve()

    if root not in path.parents or not path.is_file():
        raise FileNotFoundError

    return path


def get_pending_radiology_orders():
    return db.session.scalars(
        db.select(RadiologyOrder)
        .where(
            RadiologyOrder.status.in_(ORDER_OPEN),
            RadiologyOrder.deleted_at.is_(None),
        )
        .order_by(RadiologyOrder.ordered_at)
    ).all()


def get_today_schedule():
    today = _now().date()
    start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc)

    return db.session.scalars(
        db.select(RadiologyOrder)
        .where(
            RadiologyOrder.scheduled_at >= start,
            RadiologyOrder.scheduled_at <= end,
            RadiologyOrder.deleted_at.is_(None),
        )
        .order_by(RadiologyOrder.scheduled_at)
    ).all()


def get_reports_waiting_verification():
    return db.session.scalars(
        db.select(RadiologyReport)
        .where(
            RadiologyReport.status == "draft",
            RadiologyReport.deleted_at.is_(None),
        )
        .order_by(RadiologyReport.reported_at.desc())
    ).all()