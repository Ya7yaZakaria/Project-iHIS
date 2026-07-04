"""Central longitudinal electronic medical record models."""

from extensions import db
from .base import BaseModel


class MedicalRecord(BaseModel):
    __tablename__ = "medical_records"
    record_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), index=True)
    appointment_id = db.Column(db.String(36), db.ForeignKey("appointments.id"), index=True)
    encounter_type = db.Column(db.String(60), nullable=False, default="outpatient", index=True)
    encounter_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    chief_complaint = db.Column(db.Text)
    history = db.Column(db.Text)
    history_of_present_illness = db.Column(db.Text)
    note_format = db.Column(db.String(20), nullable=False, default="standard")
    subjective = db.Column(db.Text)
    objective = db.Column(db.Text)
    examination = db.Column(db.Text)
    assessment = db.Column(db.Text)
    plan = db.Column(db.Text)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)
    signed_at = db.Column(db.DateTime(timezone=True))
    follow_up_date = db.Column(db.Date)
    patient = db.relationship("Patient", back_populates="medical_records")
    doctor = db.relationship("Doctor", back_populates="medical_records")
    appointment = db.relationship("Appointment")
    diagnoses = db.relationship("Diagnosis", back_populates="medical_record")
    prescriptions = db.relationship("Prescription", back_populates="medical_record")
    vital_signs = db.relationship("VitalSign", back_populates="medical_record")
    nursing_notes = db.relationship("NursingNote", back_populates="medical_record")
    attachments = db.relationship("MedicalAttachment", back_populates="medical_record")


class Diagnosis(BaseModel):
    __tablename__ = "diagnoses"
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), nullable=False, index=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), index=True)
    icd10_code = db.Column(db.String(20), index=True)
    description = db.Column(db.String(255), nullable=False)
    diagnosis_type = db.Column(db.String(30), nullable=False, default="primary")
    diagnosed_at = db.Column(db.DateTime(timezone=True), nullable=False)
    resolved_at = db.Column(db.DateTime(timezone=True))
    medical_record = db.relationship("MedicalRecord", back_populates="diagnoses")


class Medication(BaseModel):
    __tablename__ = "medications"
    generic_name = db.Column(db.String(160), nullable=False, index=True)
    brand_name = db.Column(db.String(160), index=True)
    form = db.Column(db.String(60))
    strength = db.Column(db.String(80))
    route = db.Column(db.String(60))
    code = db.Column(db.String(80), unique=True, index=True)
    category = db.Column(db.String(100), index=True)
    manufacturer = db.Column(db.String(160))
    barcode = db.Column(db.String(120), unique=True, index=True)


class Prescription(BaseModel):
    __tablename__ = "prescriptions"
    prescription_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    prescribed_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="created", index=True)
    notes = db.Column(db.Text)
    pharmacy_notes = db.Column(db.Text)
    sent_at = db.Column(db.DateTime(timezone=True), index=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), index=True)
    reviewed_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    completed_at = db.Column(db.DateTime(timezone=True), index=True)
    completed_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    cancelled_at = db.Column(db.DateTime(timezone=True), index=True)
    cancelled_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    cancellation_reason = db.Column(db.Text)
    patient = db.relationship("Patient", back_populates="prescriptions")
    doctor = db.relationship("Doctor")
    medical_record = db.relationship("MedicalRecord", back_populates="prescriptions")
    items = db.relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])
    completed_by = db.relationship("User", foreign_keys=[completed_by_id])
    cancelled_by = db.relationship("User", foreign_keys=[cancelled_by_id])


class PrescriptionItem(BaseModel):
    __tablename__ = "prescription_items"
    prescription_id = db.Column(db.String(36), db.ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    medication_id = db.Column(db.String(36), db.ForeignKey("medications.id"), nullable=False, index=True)
    dose = db.Column(db.String(120), nullable=False)
    route = db.Column(db.String(60))
    frequency = db.Column(db.String(120), nullable=False)
    duration = db.Column(db.String(120))
    quantity = db.Column(db.String(80))
    requested_quantity = db.Column(db.Numeric(12, 2), nullable=False, default=1)
    dispensed_quantity = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    substitute_medication_id = db.Column(db.String(36), db.ForeignKey("medications.id"), index=True)
    substitution_note = db.Column(db.Text)
    instructions = db.Column(db.Text)
    prescription = db.relationship("Prescription", back_populates="items")
    medication = db.relationship("Medication", foreign_keys=[medication_id])
    substitute_medication = db.relationship("Medication", foreign_keys=[substitute_medication_id])
    dispensing_records = db.relationship("DispensingRecord", back_populates="prescription_item")


class MedicalAttachment(BaseModel):
    __tablename__ = "medical_attachments"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    uploaded_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False, unique=True)
    mime_type = db.Column(db.String(120), nullable=False)
    extension = db.Column(db.String(12), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    checksum_sha256 = db.Column(db.String(64), nullable=False, index=True)
    category = db.Column(db.String(60), nullable=False, default="clinical_document", index=True)
    description = db.Column(db.Text)
    patient = db.relationship("Patient", back_populates="attachments")
    medical_record = db.relationship("MedicalRecord", back_populates="attachments")
    uploaded_by = db.relationship("User")


class VitalSign(BaseModel):
    __tablename__ = "vital_signs"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    recorded_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    temperature_c = db.Column(db.Numeric(4, 1))
    pulse_bpm = db.Column(db.Integer)
    respiratory_rate = db.Column(db.Integer)
    systolic_bp = db.Column(db.Integer)
    diastolic_bp = db.Column(db.Integer)
    oxygen_saturation = db.Column(db.Numeric(5, 2))
    weight_kg = db.Column(db.Numeric(7, 2))
    height_cm = db.Column(db.Numeric(6, 2))
    pain_score = db.Column(db.Integer)
    medical_record = db.relationship("MedicalRecord", back_populates="vital_signs")


class NursingNote(BaseModel):
    __tablename__ = "nursing_notes"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    nurse_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    note_type = db.Column(db.String(60), nullable=False, default="progress")
    note = db.Column(db.Text, nullable=False)
    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    medical_record = db.relationship("MedicalRecord", back_populates="nursing_notes")
