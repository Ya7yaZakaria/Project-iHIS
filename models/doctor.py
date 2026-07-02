"""Healthcare provider and specialty models."""

from extensions import db
from .base import BaseModel


class Specialty(BaseModel):
    __tablename__ = "specialties"
    code = db.Column(db.String(40), nullable=False, unique=True, index=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    category = db.Column(db.String(60), nullable=False, default="medical", index=True)
    description = db.Column(db.String(255))
    doctors = db.relationship("Doctor", back_populates="specialty")


class Doctor(BaseModel):
    __tablename__ = "doctors"
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    specialty_id = db.Column(db.String(36), db.ForeignKey("specialties.id"), nullable=True, index=True)
    department_id = db.Column(db.String(36), db.ForeignKey("departments.id"), index=True)
    license_number = db.Column(db.String(80), nullable=True, unique=True, index=True)
    title = db.Column(db.String(80))
    qualifications = db.Column(db.JSON)
    digital_signature_path = db.Column(db.String(255))
    user = db.relationship("User", back_populates="doctor_profile")
    specialty = db.relationship("Specialty", back_populates="doctors")
    department = db.relationship("Department")
    appointments = db.relationship("Appointment", back_populates="doctor")
    medical_records = db.relationship("MedicalRecord", back_populates="doctor")
