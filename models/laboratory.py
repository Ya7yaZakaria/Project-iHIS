"""Laboratory order and result models."""

from extensions import db
from .base import BaseModel


class LabTest(BaseModel):
    __tablename__ = "lab_tests"
    code = db.Column(db.String(60), nullable=False, unique=True, index=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    unit = db.Column(db.String(40))
    reference_range = db.Column(db.String(120))
    sample_type = db.Column(db.String(80))
    turnaround_minutes = db.Column(db.Integer)
    orders = db.relationship("LabOrder", back_populates="lab_test")


class LabOrder(BaseModel):
    __tablename__ = "lab_orders"
    order_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    lab_test_id = db.Column(db.String(36), db.ForeignKey("lab_tests.id"), index=True)
    department_id = db.Column(db.String(36), db.ForeignKey("departments.id"), index=True)
    assigned_to_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    test_code = db.Column(db.String(60), index=True)
    test_name = db.Column(db.String(160), nullable=False, index=True)
    priority = db.Column(db.String(20), nullable=False, default="routine")
    status = db.Column(db.String(30), nullable=False, default="requested", index=True)
    ordered_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    specimen_type = db.Column(db.String(80))
    clinical_notes = db.Column(db.Text)
    collected_at = db.Column(db.DateTime(timezone=True), index=True)
    collected_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    processing_started_at = db.Column(db.DateTime(timezone=True), index=True)
    cancelled_at = db.Column(db.DateTime(timezone=True), index=True)
    cancelled_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    cancellation_reason = db.Column(db.Text)
    patient = db.relationship("Patient", back_populates="lab_orders")
    doctor = db.relationship("Doctor")
    medical_record = db.relationship("MedicalRecord")
    lab_test = db.relationship("LabTest", back_populates="orders")
    department = db.relationship("Department")
    assigned_to = db.relationship("User", foreign_keys=[assigned_to_id])
    collected_by = db.relationship("User", foreign_keys=[collected_by_id])
    cancelled_by = db.relationship("User", foreign_keys=[cancelled_by_id])
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
    result_type = db.Column(db.String(20), nullable=False, default="text")
    comments = db.Column(db.Text)
    resulted_at = db.Column(db.DateTime(timezone=True), index=True)
    entered_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    validated_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    verified_at = db.Column(db.DateTime(timezone=True), index=True)
    reviewed_by_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), index=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), index=True)
    attachment_name = db.Column(db.String(255))
    attachment_stored_name = db.Column(db.String(255))
    attachment_mime_type = db.Column(db.String(120))
    attachment_size = db.Column(db.Integer)
    order = db.relationship("LabOrder", back_populates="results")
    entered_by = db.relationship("User", foreign_keys=[entered_by_id])
    verified_by = db.relationship("User", foreign_keys=[validated_by_id])
    reviewed_by = db.relationship("Doctor", foreign_keys=[reviewed_by_id])
