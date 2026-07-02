"""Dentistry extension models linked to the central patient and EMR."""

from extensions import db
from .base import BaseModel


class DentalSpecialty(BaseModel):
    __tablename__ = "dental_specialties"
    code = db.Column(db.String(40), nullable=False, unique=True, index=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    description = db.Column(db.String(255))


class Dentist(BaseModel):
    __tablename__ = "dentists"
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    dental_specialty_id = db.Column(db.String(36), db.ForeignKey("dental_specialties.id"), nullable=False, index=True)
    department_id = db.Column(db.String(36), db.ForeignKey("departments.id"), index=True)
    license_number = db.Column(db.String(80), nullable=False, unique=True, index=True)
    qualifications = db.Column(db.JSON)
    user = db.relationship("User")
    specialty = db.relationship("DentalSpecialty")


class DentalRecord(BaseModel):
    __tablename__ = "dental_records"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    dentist_id = db.Column(db.String(36), db.ForeignKey("dentists.id"), index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    visit_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    chief_complaint = db.Column(db.Text)
    dental_history = db.Column(db.Text)
    examination = db.Column(db.Text)
    treatment_plan = db.Column(db.Text)
    progress_notes = db.Column(db.Text)
    status = db.Column(db.String(30), nullable=False, default="active", index=True)
    patient = db.relationship("Patient")
    dentist = db.relationship("Dentist")
    medical_record = db.relationship("MedicalRecord")
    charts = db.relationship("DentalChart", back_populates="dental_record")
    procedures = db.relationship("DentalProcedure", back_populates="dental_record")


class DentalChart(BaseModel):
    __tablename__ = "dental_charts"
    __table_args__ = (db.UniqueConstraint("dental_record_id", "tooth_number", "numbering_system", name="uq_dental_chart_tooth"),)
    dental_record_id = db.Column(db.String(36), db.ForeignKey("dental_records.id"), nullable=False, index=True)
    tooth_number = db.Column(db.String(12), nullable=False, index=True)
    numbering_system = db.Column(db.String(20), nullable=False, default="FDI")
    condition = db.Column(db.String(80), nullable=False, index=True)
    surfaces = db.Column(db.JSON)
    periodontal_data = db.Column(db.JSON)
    notes = db.Column(db.Text)
    dental_record = db.relationship("DentalRecord", back_populates="charts")


class DentalProcedure(BaseModel):
    __tablename__ = "dental_procedures"
    dental_record_id = db.Column(db.String(36), db.ForeignKey("dental_records.id"), nullable=False, index=True)
    dentist_id = db.Column(db.String(36), db.ForeignKey("dentists.id"), nullable=False, index=True)
    tooth_number = db.Column(db.String(12), index=True)
    procedure_code = db.Column(db.String(40), index=True)
    procedure_name = db.Column(db.String(160), nullable=False)
    performed_at = db.Column(db.DateTime(timezone=True), index=True)
    status = db.Column(db.String(30), nullable=False, default="planned", index=True)
    notes = db.Column(db.Text)
    dental_record = db.relationship("DentalRecord", back_populates="procedures")


class DentalImage(BaseModel):
    __tablename__ = "dental_images"
    dental_record_id = db.Column(db.String(36), db.ForeignKey("dental_records.id"), nullable=False, index=True)
    image_type = db.Column(db.String(60), nullable=False, index=True)
    file_path = db.Column(db.String(255), nullable=False)
    tooth_number = db.Column(db.String(12), index=True)
    captured_at = db.Column(db.DateTime(timezone=True), index=True)
    description = db.Column(db.Text)


class OrthodonticCase(BaseModel):
    __tablename__ = "orthodontic_cases"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    dentist_id = db.Column(db.String(36), db.ForeignKey("dentists.id"), nullable=False, index=True)
    dental_record_id = db.Column(db.String(36), db.ForeignKey("dental_records.id"), index=True)
    diagnosis = db.Column(db.Text)
    appliance_type = db.Column(db.String(100))
    treatment_plan = db.Column(db.Text)
    start_date = db.Column(db.Date)
    expected_end_date = db.Column(db.Date)
    actual_end_date = db.Column(db.Date)
    status = db.Column(db.String(30), nullable=False, default="planned", index=True)
