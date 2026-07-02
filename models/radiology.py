"""Radiology order and report models."""

from extensions import db
from .base import BaseModel


class RadiologyOrder(BaseModel):
    __tablename__ = "radiology_orders"
    order_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    modality = db.Column(db.String(40), nullable=False, index=True)
    body_part = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="routine")
    status = db.Column(db.String(30), nullable=False, default="requested", index=True)
    ordered_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    clinical_indication = db.Column(db.Text)
    dicom_study_uid = db.Column(db.String(128), unique=True, index=True)
    patient = db.relationship("Patient", back_populates="radiology_orders")
    reports = db.relationship("RadiologyReport", back_populates="order")


class RadiologyReport(BaseModel):
    __tablename__ = "radiology_reports"
    radiology_order_id = db.Column(db.String(36), db.ForeignKey("radiology_orders.id"), nullable=False, index=True)
    radiologist_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), index=True)
    findings = db.Column(db.Text)
    impression = db.Column(db.Text)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)
    is_critical = db.Column(db.Boolean, nullable=False, default=False, index=True)
    reported_at = db.Column(db.DateTime(timezone=True), index=True)
    image_links = db.Column(db.JSON)
    order = db.relationship("RadiologyOrder", back_populates="reports")
