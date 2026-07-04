"""Patient and appointment models."""

from extensions import db
from .base import BaseModel


class Patient(BaseModel):
    __tablename__ = "patients"

    medical_record_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), unique=True, index=True)
    first_name = db.Column(db.String(100), nullable=False, index=True)
    last_name = db.Column(db.String(100), nullable=False, index=True)
    date_of_birth = db.Column(db.Date, nullable=False, index=True)
    sex_at_birth = db.Column(db.String(30), nullable=False)
    blood_type = db.Column(db.String(5))
    phone = db.Column(db.String(40), index=True)
    email = db.Column(db.String(255), index=True)
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.JSON)
    allergies = db.Column(db.JSON)
    chronic_conditions = db.Column(db.JSON)
    surgical_history = db.Column(db.JSON)
    family_history = db.Column(db.JSON)
    vaccination_history = db.Column(db.JSON)

    user = db.relationship("User", foreign_keys=[user_id])
    appointments = db.relationship("Appointment", back_populates="patient")
    medical_records = db.relationship("MedicalRecord", back_populates="patient")
    prescriptions = db.relationship("Prescription", back_populates="patient")
    lab_orders = db.relationship("LabOrder", back_populates="patient")
    radiology_orders = db.relationship("RadiologyOrder", back_populates="patient")
    womens_health_profile = db.relationship(
        "WomensHealthProfile",
        back_populates="patient",
        uselist=False,
    )
    attachments = db.relationship("MedicalAttachment", back_populates="patient")


class Appointment(BaseModel):
    __tablename__ = "appointments"

    __table_args__ = (
        db.Index("ix_appointments_doctor_start", "doctor_id", "scheduled_start"),
        db.CheckConstraint(
            "scheduled_end IS NULL OR scheduled_end > scheduled_start",
            name="ck_appointment_time_order",
        ),
    )

    appointment_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), index=True)
    department_id = db.Column(db.String(36), db.ForeignKey("departments.id"), index=True)

    scheduled_start = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    scheduled_end = db.Column(db.DateTime(timezone=True))

    appointment_type = db.Column(db.String(60), nullable=False, default="consultation")
    status = db.Column(db.String(30), nullable=False, default="booked", index=True)
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)

    arrival_time = db.Column(db.DateTime(timezone=True), index=True)
    consultation_started_at = db.Column(db.DateTime(timezone=True), index=True)
    consultation_completed_at = db.Column(db.DateTime(timezone=True), index=True)

    cancelled_at = db.Column(db.DateTime(timezone=True), index=True)
    cancelled_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    cancellation_reason = db.Column(db.Text)

    queue_number = db.Column(db.Integer, index=True)
    reception_notes = db.Column(db.Text)

    follow_up_of_id = db.Column(db.String(36), db.ForeignKey("appointments.id"), index=True)

    patient = db.relationship("Patient", back_populates="appointments")
    doctor = db.relationship("Doctor", back_populates="appointments")
    department = db.relationship("Department")

    cancelled_by = db.relationship("User", foreign_keys=[cancelled_by_id])
    follow_up_of = db.relationship(
        "Appointment",
        remote_side="Appointment.id",
        foreign_keys=[follow_up_of_id],
        post_update=True,
    )
