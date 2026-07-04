"""Simple Nursing module models.

Phase 13 keeps nursing practical and EMR-integrated:
- Reuse existing EMR VitalSign.
- Reuse existing EMR NursingNote.
- Add only medication administration and care plans.
"""

from extensions import db
from .base import BaseModel


class MedicationAdministration(BaseModel):
    __tablename__ = "medication_administrations"

    patient_id = db.Column(
        db.String(36),
        db.ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )
    medical_record_id = db.Column(
        db.String(36),
        db.ForeignKey("medical_records.id"),
        nullable=True,
        index=True,
    )
    prescription_item_id = db.Column(
        db.String(36),
        db.ForeignKey("prescription_items.id"),
        nullable=True,
        index=True,
    )

    medication_name = db.Column(db.String(160), nullable=False, index=True)
    dose = db.Column(db.String(120), nullable=True)
    scheduled_time = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    given_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)

    status = db.Column(db.String(30), nullable=False, default="given", index=True)
    given_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)

    missed_reason = db.Column(db.Text)
    patient_reaction = db.Column(db.Text)
    notes = db.Column(db.Text)

    patient = db.relationship("Patient")
    medical_record = db.relationship("MedicalRecord")
    prescription_item = db.relationship("PrescriptionItem")
    given_by = db.relationship("User", foreign_keys=[given_by_id])


class NursingCarePlan(BaseModel):
    __tablename__ = "nursing_care_plans"

    patient_id = db.Column(
        db.String(36),
        db.ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )
    medical_record_id = db.Column(
        db.String(36),
        db.ForeignKey("medical_records.id"),
        nullable=True,
        index=True,
    )
    created_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)

    nursing_diagnosis = db.Column(db.Text, nullable=False)
    goals = db.Column(db.Text, nullable=False)
    interventions = db.Column(db.Text, nullable=False)
    evaluation = db.Column(db.Text)

    status = db.Column(db.String(30), nullable=False, default="active", index=True)

    patient = db.relationship("Patient")
    medical_record = db.relationship("MedicalRecord")
    created_by = db.relationship("User", foreign_keys=[created_by_id])