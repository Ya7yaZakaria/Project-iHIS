"""Laboratory order and result models."""

from extensions import db
from .base import BaseModel


class LabOrder(BaseModel):
    __tablename__ = "lab_orders"
    order_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    test_code = db.Column(db.String(60), index=True)
    test_name = db.Column(db.String(160), nullable=False, index=True)
    priority = db.Column(db.String(20), nullable=False, default="routine")
    status = db.Column(db.String(30), nullable=False, default="requested", index=True)
    ordered_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    specimen_type = db.Column(db.String(80))
    clinical_notes = db.Column(db.Text)
    patient = db.relationship("Patient", back_populates="lab_orders")
    doctor = db.relationship("Doctor")
    medical_record = db.relationship("MedicalRecord")
    results = db.relationship("LabResult", back_populates="order")


class LabResult(BaseModel):
    __tablename__ = "lab_results"
    lab_order_id = db.Column(db.String(36), db.ForeignKey("lab_orders.id"), nullable=False, index=True)
    component_name = db.Column(db.String(160), nullable=False, index=True)
    value_text = db.Column(db.String(255))
    value_numeric = db.Column(db.Numeric(18, 6))
    unit = db.Column(db.String(40))
    reference_range = db.Column(db.String(120))
    abnormal_flag = db.Column(db.String(20), index=True)
    is_critical = db.Column(db.Boolean, nullable=False, default=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="preliminary", index=True)
    resulted_at = db.Column(db.DateTime(timezone=True), index=True)
    validated_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    order = db.relationship("LabOrder", back_populates="results")
