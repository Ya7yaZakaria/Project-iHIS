"""Validated forms for the central EMR workflows."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (DateField, DateTimeLocalField, DecimalField, IntegerField,
                     SelectField, StringField, SubmitField, TextAreaField)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class PatientForm(FlaskForm):
    medical_record_number=StringField("MRN override",validators=[Optional(),Length(max=50)])
    first_name=StringField("First name",validators=[DataRequired(),Length(max=100)])
    last_name=StringField("Last name",validators=[DataRequired(),Length(max=100)])
    date_of_birth=DateField("Date of birth",validators=[DataRequired()])
    sex_at_birth=SelectField("Sex at birth",choices=[("female","Female"),("male","Male"),("intersex","Intersex"),("unknown","Unknown")],validators=[DataRequired()])
    blood_type=SelectField("Blood type",choices=[("","Unknown"),("A+","A+"),("A-","A-"),("B+","B+"),("B-","B-"),("AB+","AB+"),("AB-","AB-"),("O+","O+"),("O-","O-")],validators=[Optional()])
    phone=StringField("Phone",validators=[Optional(),Length(max=40)])
    email=StringField("Email",validators=[Optional(),Length(max=255)])
    address=TextAreaField("Address",validators=[Optional()])
    allergies=TextAreaField("Allergies (one per line)",validators=[Optional()])
    chronic_conditions=TextAreaField("Chronic diseases (one per line)",validators=[Optional()])
    surgical_history=TextAreaField("Surgical history (one per line)",validators=[Optional()])
    family_history=TextAreaField("Family history (one per line)",validators=[Optional()])
    vaccination_history=TextAreaField("Vaccinations (one per line)",validators=[Optional()])
    submit=SubmitField("Save patient")


class VisitForm(FlaskForm):
    encounter_type=SelectField("Visit type",choices=[("outpatient","Outpatient"),("inpatient","Inpatient"),("emergency","Emergency"),("telemedicine","Telemedicine"),("follow_up","Follow-up")],validators=[DataRequired()])
    encounter_at=DateTimeLocalField("Visit date/time",format="%Y-%m-%dT%H:%M",validators=[Optional()])
    note_format=SelectField("Note format",choices=[("standard","Standard clinical note"),("soap","SOAP")])
    chief_complaint=TextAreaField("Chief complaint",validators=[Optional()])
    history_of_present_illness=TextAreaField("History of present illness",validators=[Optional()])
    history=TextAreaField("Relevant history",validators=[Optional()])
    subjective=TextAreaField("Subjective",validators=[Optional()])
    objective=TextAreaField("Objective",validators=[Optional()])
    examination=TextAreaField("Examination",validators=[Optional()])
    assessment=TextAreaField("Assessment",validators=[Optional()])
    plan=TextAreaField("Plan",validators=[Optional()])
    follow_up_date=DateField("Follow-up date",validators=[Optional()])
    submit=SubmitField("Save visit")


class DiagnosisForm(FlaskForm):
    diagnosis_type=SelectField("Type",choices=[("primary","Primary"),("secondary","Secondary")])
    icd10_code=StringField("ICD-10 code",validators=[Optional(),Length(max=20)])
    description=StringField("Diagnosis",validators=[DataRequired(),Length(max=255)])
    notes=TextAreaField("Notes",validators=[Optional()])
    submit=SubmitField("Add diagnosis")


class PrescriptionForm(FlaskForm):
    notes=TextAreaField("Prescription notes",validators=[Optional()])
    generic_name=StringField("Medication",validators=[DataRequired(),Length(max=160)])
    brand_name=StringField("Brand",validators=[Optional(),Length(max=160)])
    strength=StringField("Strength",validators=[Optional(),Length(max=80)])
    dose=StringField("Dose",validators=[DataRequired(),Length(max=120)])
    route=StringField("Route",validators=[Optional(),Length(max=60)])
    frequency=StringField("Frequency",validators=[DataRequired(),Length(max=120)])
    duration=StringField("Duration",validators=[Optional(),Length(max=120)])
    quantity=DecimalField("Quantity",places=2,validators=[DataRequired(),NumberRange(min=0.01)])
    instructions=TextAreaField("Instructions",validators=[Optional()])
    submit=SubmitField("Create prescription")


class OrderForm(FlaskForm):
    order_type=SelectField("Order type",choices=[("lab","Laboratory"),("radiology","Radiology")])
    lab_test_id=SelectField("Catalog test",choices=[],validators=[Optional()])
    test_name=StringField("Lab test name",validators=[Optional(),Length(max=160)])
    test_code=StringField("Lab test code",validators=[Optional(),Length(max=60)])
    specimen_type=StringField("Specimen",validators=[Optional(),Length(max=80)])
    modality=SelectField("Modality",choices=[("","Select"),("X-Ray","X-Ray"),("CT","CT"),("MRI","MRI"),("Ultrasound","Ultrasound"),("Mammography","Mammography")],validators=[Optional()])
    body_part=StringField("Body part",validators=[Optional(),Length(max=100)])
    priority=SelectField("Priority",choices=[("routine","Routine"),("urgent","Urgent"),("stat","STAT")])
    clinical_notes=TextAreaField("Clinical indication / notes",validators=[Optional()])
    submit=SubmitField("Create order")


class AttachmentForm(FlaskForm):
    file=FileField("Medical document",validators=[FileRequired()])
    category=SelectField("Category",choices=[("clinical_document","Clinical document"),("image","Medical image"),("referral","Referral"),("consent","Consent"),("other","Other")])
    medical_record_id=SelectField("Link to visit",validators=[Optional()])
    description=TextAreaField("Description",validators=[Optional()])
    submit=SubmitField("Upload securely")


class VitalSignForm(FlaskForm):
    temperature_c=DecimalField("Temperature °C",validators=[Optional()]); pulse_bpm=IntegerField("Pulse",validators=[Optional()])
    respiratory_rate=IntegerField("Respiratory rate",validators=[Optional()]); systolic_bp=IntegerField("Systolic BP",validators=[Optional()])
    diastolic_bp=IntegerField("Diastolic BP",validators=[Optional()]); oxygen_saturation=DecimalField("Oxygen saturation",validators=[Optional()])
    weight_kg=DecimalField("Weight kg",validators=[Optional()]); height_cm=DecimalField("Height cm",validators=[Optional()]); pain_score=IntegerField("Pain score",validators=[Optional()])
    submit=SubmitField("Record vitals")


class NursingNoteForm(FlaskForm):
    note_type=SelectField("Note type",choices=[("progress","Progress"),("handover","Handover"),("care_plan","Care plan")])
    note=TextAreaField("Nursing note",validators=[DataRequired()]); submit=SubmitField("Add nursing note")


def lines(value): return [line.strip() for line in (value or "").splitlines() if line.strip()]
def unlines(value): return "\n".join(value or [])
