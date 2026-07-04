"""Forms for Women's Health clinic workflows."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (DateField, DateTimeLocalField, DecimalField, IntegerField,
                     SelectField, StringField, SubmitField, TextAreaField)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class ProfileForm(FlaskForm):
    ob_gyn_summary=TextAreaField("OB/GYN summary",validators=[Optional()]); menarche_age=IntegerField("Menarche age",validators=[Optional(),NumberRange(min=5,max=30)])
    cycle_pattern=StringField("Cycle pattern",validators=[Optional(),Length(max=80)]); blood_group=StringField("Blood group",validators=[Optional(),Length(max=5)])
    rhesus_status=StringField("Rhesus",validators=[Optional(),Length(max=12)]); menstrual_history=TextAreaField("Menstrual history",validators=[Optional()])
    contraception_history=TextAreaField("Contraception history",validators=[Optional()]); infertility_history=TextAreaField("Infertility history",validators=[Optional()])
    surgical_history=TextAreaField("Surgical history",validators=[Optional()]); risk_flags=TextAreaField("Risk flags",validators=[Optional()]); submit=SubmitField("Save profile")


class PregnancyForm(FlaskForm):
    lmp=DateField("LMP",validators=[Optional()]); estimated_due_date=DateField("EDD override",validators=[Optional()])
    gravida=IntegerField("Gravidity",validators=[Optional(),NumberRange(min=0)]); para=IntegerField("Parity",validators=[Optional(),NumberRange(min=0)])
    abortions=IntegerField("Abortions",default=0,validators=[NumberRange(min=0)]); living_children=IntegerField("Living",default=0,validators=[NumberRange(min=0)])
    previous_cs_count=IntegerField("Previous CS",default=0,validators=[NumberRange(min=0)]); previous_vaginal_births=IntegerField("Previous vaginal births",default=0,validators=[NumberRange(min=0)])
    risk_category=SelectField("Risk category",choices=[("low","Low"),("moderate","Moderate"),("high","High")]); high_risk_flags=TextAreaField("High-risk flags",validators=[Optional()]); submit=SubmitField("Create pregnancy")


class AntenatalVisitForm(FlaskForm):
    visit_at=DateTimeLocalField("Visit date",format="%Y-%m-%dT%H:%M",validators=[Optional()]); weight_kg=DecimalField("Weight kg",validators=[Optional(),NumberRange(min=1)])
    systolic_bp=IntegerField("Systolic BP",validators=[Optional()]); diastolic_bp=IntegerField("Diastolic BP",validators=[Optional()])
    urine_findings=StringField("Urine findings",validators=[Optional()]); fetal_heart_rate=IntegerField("Fetal heart rate",validators=[Optional()])
    fundal_height_cm=DecimalField("Fundal height cm",validators=[Optional()]); fetal_movement=StringField("Fetal movement",validators=[Optional()])
    presentation=StringField("Presentation",validators=[Optional()]); complaint=TextAreaField("Complaint",validators=[Optional()])
    assessment=TextAreaField("Assessment",validators=[Optional()]); plan=TextAreaField("Plan",validators=[Optional()]); follow_up_date=DateField("Follow-up",validators=[Optional()]); submit=SubmitField("Save ANC visit")


class GynecologyJourneyForm(FlaskForm):
    primary_condition=StringField("Primary condition",validators=[DataRequired(),Length(max=160)]); summary=TextAreaField("Summary",validators=[Optional()]); submit=SubmitField("Create journey")


class GynecologyVisitForm(FlaskForm):
    symptoms=TextAreaField("Complaint / symptoms",validators=[Optional()]); examination=TextAreaField("Examination",validators=[Optional()]); diagnosis=TextAreaField("Diagnosis",validators=[Optional()])
    assessment=TextAreaField("Assessment",validators=[Optional()]); plan=TextAreaField("Plan",validators=[Optional()]); procedures=TextAreaField("Procedures",validators=[Optional()]); follow_up_date=DateField("Follow-up",validators=[Optional()]); submit=SubmitField("Add visit")


class InfertilityJourneyForm(FlaskForm):
    infertility_type=SelectField("Type",choices=[("primary","Primary"),("secondary","Secondary")]); duration_months=IntegerField("Duration months",validators=[Optional(),NumberRange(min=0)])
    female_factor=TextAreaField("Female factor",validators=[Optional()]); male_factor=TextAreaField("Male factor",validators=[Optional()]); investigations=TextAreaField("Investigations",validators=[Optional()]); treatment_plan=TextAreaField("Treatment plan",validators=[Optional()]); submit=SubmitField("Create journey")


class PartnerForm(FlaskForm):
    first_name=StringField("First name",validators=[DataRequired()]); last_name=StringField("Last name",validators=[DataRequired()]); date_of_birth=DateField("Date of birth",validators=[Optional()]); fertility_history=TextAreaField("Fertility history",validators=[Optional()]); submit=SubmitField("Add partner")


class SemenAnalysisForm(FlaskForm):
    volume_ml=DecimalField("Volume ml",validators=[Optional()]); concentration_million_ml=DecimalField("Concentration million/ml",validators=[Optional()]); total_motility_percent=DecimalField("Total motility %",validators=[Optional()]); progressive_motility_percent=DecimalField("Progressive motility %",validators=[Optional()]); normal_morphology_percent=DecimalField("Normal morphology %",validators=[Optional()]); interpretation=TextAreaField("Interpretation",validators=[Optional()]); submit=SubmitField("Add semen analysis")


class InfertilityCycleForm(FlaskForm):
    cycle_type=SelectField("Cycle type",choices=[("ovulation_induction","Ovulation induction / OITI"),("iui","IUI"),("monitoring","Monitoring")]); cycle_start_date=DateField("LMP / cycle start",validators=[DataRequired()]); protocol=TextAreaField("Protocol and medications",validators=[Optional()]); timed_intercourse_advice=TextAreaField("Timed intercourse advice",validators=[Optional()]); submit=SubmitField("Create cycle")


class FolliculometryForm(FlaskForm):
    scan_at=DateTimeLocalField("Scan date",format="%Y-%m-%dT%H:%M",validators=[Optional()]); endometrium_mm=DecimalField("Endometrium mm",validators=[Optional()]); endometrium_pattern=StringField("Endometrium pattern",validators=[Optional()]); notes=TextAreaField("Notes",validators=[Optional()]); ovary=SelectField("Ovary",choices=[("right","Right"),("left","Left")]); follicle_number=IntegerField("Follicle number",validators=[Optional(),NumberRange(min=1)]); diameter_mm=DecimalField("Diameter mm",validators=[Optional(),NumberRange(min=0)]); submit=SubmitField("Add folliculometry")


class IUIForm(FlaskForm):
    partner_id=SelectField("Partner",validators=[Optional()]); performed_at=DateTimeLocalField("IUI date",format="%Y-%m-%dT%H:%M",validators=[Optional()]); trigger_at=DateTimeLocalField("Trigger",format="%Y-%m-%dT%H:%M",validators=[Optional()]); stimulation_protocol=TextAreaField("Stimulation protocol",validators=[Optional()]); semen_preparation_summary=TextAreaField("Semen preparation",validators=[Optional()]); post_wash_count=DecimalField("Post-wash count",validators=[Optional()]); luteal_support=TextAreaField("Luteal support",validators=[Optional()]); pregnancy_test_date=DateField("Pregnancy test date",validators=[Optional()]); outcome=StringField("Outcome",validators=[Optional()]); submit=SubmitField("Create IUI")


class UltrasoundForm(FlaskForm):
    profile_id=SelectField("Patient profile",validators=[DataRequired()]); pregnancy_id=SelectField("Pregnancy",validators=[Optional()]); pregnancy_visit_id=SelectField("Pregnancy visit",validators=[Optional()]); antenatal_visit_id=SelectField("ANC visit",validators=[Optional()]); gynecology_journey_id=SelectField("Gynecology journey",validators=[Optional()]); gynecology_visit_id=SelectField("Gynecology visit",validators=[Optional()]); infertility_journey_id=SelectField("Infertility journey",validators=[Optional()]); scan_type=SelectField("Scan type",choices=[("obstetric","OB ultrasound"),("gynecology","Gyn ultrasound"),("folliculometry","Folliculometry"),("fetal_biometry","Fetal biometry"),("fetal_doppler","Fetal Doppler")]); performed_at=DateTimeLocalField("Performed at",format="%Y-%m-%dT%H:%M",validators=[Optional()]); placenta=StringField("Placenta",validators=[Optional()]); liquor=StringField("Liquor",validators=[Optional()]); cervical_length_mm=DecimalField("Cervical length mm",validators=[Optional()]); biparietal_diameter_mm=DecimalField("BPD mm",validators=[Optional()]); head_circumference_mm=DecimalField("HC mm",validators=[Optional()]); abdominal_circumference_mm=DecimalField("AC mm",validators=[Optional()]); femur_length_mm=DecimalField("FL mm",validators=[Optional()]); estimated_fetal_weight_g=DecimalField("Estimated fetal weight g",validators=[Optional()]); doppler_vessel=StringField("Doppler vessel",validators=[Optional()]); pulsatility_index=DecimalField("Doppler PI",validators=[Optional()]); resistance_index=DecimalField("Doppler RI",validators=[Optional()]); systolic_diastolic_ratio=DecimalField("Doppler S/D",validators=[Optional()]); peak_systolic_velocity=DecimalField("Peak systolic velocity",validators=[Optional()]); cerebroplacental_ratio=DecimalField("CPR",validators=[Optional()]); doppler_interpretation=StringField("Doppler interpretation",validators=[Optional()]); findings=TextAreaField("Findings",validators=[Optional()]); impression=TextAreaField("Impression",validators=[DataRequired()]); file=FileField("Image/report",validators=[Optional(),FileAllowed(["pdf","png","jpg","jpeg","webp"])]); submit=SubmitField("Create ultrasound")


class DeliveryForm(FlaskForm):
    delivered_at=DateTimeLocalField("Delivered at",format="%Y-%m-%dT%H:%M",validators=[DataRequired()]); delivery_mode=StringField("Delivery mode",validators=[DataRequired()]); outcome=StringField("Outcome",validators=[DataRequired()]); indication=TextAreaField("Indication",validators=[Optional()]); place_of_delivery=StringField("Place",validators=[Optional()]); submit=SubmitField("Record delivery")


class PostpartumForm(FlaskForm):
    maternal_assessment=TextAreaField("Maternal assessment",validators=[Optional()]); wound_assessment=TextAreaField("Wound assessment",validators=[Optional()]); lactation_status=StringField("Lactation",validators=[Optional()]); contraception_plan=StringField("Contraception plan",validators=[Optional()]); follow_up_plan=TextAreaField("Plan",validators=[Optional()]); follow_up_date=DateField("Follow-up date",validators=[Optional()]); submit=SubmitField("Add postpartum visit")


class SignForm(FlaskForm): submit=SubmitField("Sign and release")
