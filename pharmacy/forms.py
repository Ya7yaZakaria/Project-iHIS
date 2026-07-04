"""Validated forms for pharmacy catalog, dispensing, and inventory."""

from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateField, DecimalField, SelectField,
                     StringField, SubmitField, TextAreaField)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class MedicationForm(FlaskForm):
    generic_name = StringField("Generic name", validators=[DataRequired(), Length(max=160)])
    brand_name = StringField("Brand name", validators=[Optional(), Length(max=160)])
    strength = StringField("Strength", validators=[Optional(), Length(max=80)])
    dosage_form = StringField("Dosage form", validators=[Optional(), Length(max=60)])
    route = StringField("Route", validators=[Optional(), Length(max=60)])
    category = StringField("Category", validators=[Optional(), Length(max=100)])
    manufacturer = StringField("Manufacturer", validators=[Optional(), Length(max=160)])
    code = StringField("Catalog code", validators=[Optional(), Length(max=80)])
    barcode = StringField("Barcode placeholder", validators=[Optional(), Length(max=120)])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save medication")


class ReviewPrescriptionForm(FlaskForm):
    notes = TextAreaField("Pharmacist notes", validators=[Optional(), Length(max=3000)])
    submit = SubmitField("Start review")


class DispenseForm(FlaskForm):
    item_id = SelectField("Prescription item", validators=[DataRequired()])
    quantity = DecimalField("Quantity to dispense", places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    inventory_batch_id = SelectField("Batch (blank uses FEFO)", validators=[Optional()])
    substitute_medication_id = SelectField("Substitute medication placeholder", validators=[Optional()])
    substitution_note = TextAreaField("Substitution note", validators=[Optional(), Length(max=2000)])
    notes = TextAreaField("Pharmacist notes", validators=[Optional(), Length(max=3000)])
    submit = SubmitField("Dispense")


class CompleteDispensingForm(FlaskForm):
    notes = TextAreaField("Completion notes", validators=[Optional(), Length(max=3000)])
    submit = SubmitField("Mark prescription complete")


class CancelPrescriptionForm(FlaskForm):
    reason = TextAreaField("Cancellation reason", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Cancel prescription")


class AddStockForm(FlaskForm):
    medication_id = SelectField("Medication", validators=[DataRequired()])
    batch_number = StringField("Batch number", validators=[DataRequired(), Length(max=80)])
    quantity = DecimalField("Quantity", places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    reorder_level = DecimalField("Low-stock threshold", places=2, default=0, validators=[DataRequired(), NumberRange(min=0)])
    expiry_date = DateField("Expiry date", validators=[Optional()])
    supplier = StringField("Supplier placeholder", validators=[Optional(), Length(max=160)])
    unit_cost = DecimalField("Unit cost", places=2, validators=[Optional(), NumberRange(min=0)])
    location = StringField("Location", validators=[Optional(), Length(max=120)])
    submit = SubmitField("Add stock")
