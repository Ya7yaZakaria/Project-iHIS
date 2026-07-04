"""Radiology order, imaging catalog, report, and attachment models."""

from extensions import db
from .base import BaseModel


class ImagingStudy(BaseModel):
    __tablename__ = "imaging_studies"

    name = db.Column(db.String(160), nullable=False, unique=True, index=True)
    modality = db.Column(db.String(40), nullable=False, index=True)
    body_region = db.Column(db.String(120), nullable=False, index=True)
    preparation_instructions = db.Column(db.Text)
    description = db.Column(db.Text)


class RadiologyOrder(BaseModel):
    __tablename__ = "radiology_orders"

    order_number = db.Column(db.String(50), nullable=False, unique=True, index=True)

    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)

    imaging_study_id = db.Column(db.String(36), db.ForeignKey("imaging_studies.id"), index=True)
    assigned_radiology_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)

    modality = db.Column(db.String(40), nullable=False, index=True)
    body_part = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="routine", index=True)
    status = db.Column(db.String(30), nullable=False, default="requested", index=True)

    ordered_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    scheduled_at = db.Column(db.DateTime(timezone=True), index=True)
    patient_arrived_at = db.Column(db.DateTime(timezone=True), index=True)
    imaging_performed_at = db.Column(db.DateTime(timezone=True), index=True)
    cancelled_at = db.Column(db.DateTime(timezone=True), index=True)

    clinical_indication = db.Column(db.Text)
    cancellation_reason = db.Column(db.Text)
    urgent_finding_flag = db.Column(db.Boolean, nullable=False, default=False, index=True)

    dicom_study_uid = db.Column(db.String(128), unique=True, index=True)

    patient = db.relationship("Patient", back_populates="radiology_orders")
    doctor = db.relationship("Doctor", foreign_keys=[doctor_id])
    medical_record = db.relationship("MedicalRecord")
    imaging_study = db.relationship("ImagingStudy")
    assigned_radiology_user = db.relationship("User", foreign_keys=[assigned_radiology_user_id])

    reports = db.relationship(
        "RadiologyReport",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    attachments = db.relationship(
        "RadiologyAttachment",
        back_populates="order",
        cascade="all, delete-orphan",
    )


class RadiologyReport(BaseModel):
    __tablename__ = "radiology_reports"

    radiology_order_id = db.Column(
        db.String(36),
        db.ForeignKey("radiology_orders.id"),
        nullable=False,
        index=True,
    )
    radiologist_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), index=True)
    verified_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    reviewed_by_doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), index=True)

    clinical_indication = db.Column(db.Text)
    technique = db.Column(db.Text)
    findings = db.Column(db.Text)
    impression = db.Column(db.Text)
    recommendations = db.Column(db.Text)

    status = db.Column(db.String(30), nullable=False, default="draft", index=True)
    is_abnormal = db.Column(db.Boolean, nullable=False, default=False, index=True)
    is_critical = db.Column(db.Boolean, nullable=False, default=False, index=True)

    reported_at = db.Column(db.DateTime(timezone=True), index=True)
    verified_at = db.Column(db.DateTime(timezone=True), index=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), index=True)

    image_links = db.Column(db.JSON)

    order = db.relationship("RadiologyOrder", back_populates="reports")
    radiologist = db.relationship("Doctor", foreign_keys=[radiologist_id])
    verified_by = db.relationship("User", foreign_keys=[verified_by_id])
    reviewed_by_doctor = db.relationship("Doctor", foreign_keys=[reviewed_by_doctor_id])


class RadiologyAttachment(BaseModel):
    __tablename__ = "radiology_attachments"

    radiology_order_id = db.Column(
        db.String(36),
        db.ForeignKey("radiology_orders.id"),
        nullable=False,
        index=True,
    )
    uploaded_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)

    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False, unique=True)
    mime_type = db.Column(db.String(120), nullable=False)
    extension = db.Column(db.String(12), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    checksum_sha256 = db.Column(db.String(64), nullable=False, index=True)

    category = db.Column(db.String(60), nullable=False, default="image_or_report", index=True)
    description = db.Column(db.Text)

    order = db.relationship("RadiologyOrder", back_populates="attachments")
    uploaded_by = db.relationship("User", foreign_keys=[uploaded_by_id])