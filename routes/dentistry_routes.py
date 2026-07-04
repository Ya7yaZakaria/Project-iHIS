"""Dentistry module routes and views."""
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from auth.decorators import login_required
from extensions import db
from models import DentalRecord, Patient
from services.dentistry import (add_dental_procedure, build_dental_timeline,
                                create_dental_record, create_orthodontic_case,
                                update_dental_chart, update_dental_record,
                                update_orthodontic_progress, upload_dental_image)


dentistry_bp = Blueprint("dentistry", __name__, url_prefix="/dentistry")


def _patient(patient_id):
    return db.get_or_404(Patient, patient_id)


def _record(record_id):
    return db.get_or_404(DentalRecord, record_id)


def _can_manage_dentistry():
    return current_user.has_role("Super Admin", "Admin", "Dentist") or current_user.has_role("Doctor")


def _can_view_record(record):
    if current_user.has_role("Super Admin", "Admin", "Dentist") or current_user.has_role("Doctor"):
        return True
    if current_user.has_role("Patient"):
        patient = db.session.scalar(db.select(Patient).where(Patient.user_id == current_user.id))
        return bool(patient and record.patient_id == patient.id and record.status in {"active", "completed"})
    return False


@dentistry_bp.get("")
@dentistry_bp.get("/")
@login_required
def index():
    if current_user.has_role("Receptionist"):
        abort(403)
    records = db.session.scalars(db.select(DentalRecord).where(DentalRecord.deleted_at.is_(None)).order_by(DentalRecord.visit_at.desc())).all()
    return render_template("dentistry/dashboard.html", records=records, timeline=build_dental_timeline(records[0]) if records else [])


@dentistry_bp.get("/patients/<patient_id>")
@login_required
def patient_records(patient_id):
    patient = _patient(patient_id)
    if current_user.has_role("Patient") and patient.user_id != current_user.id:
        abort(403)
    if current_user.has_role("Receptionist"):
        abort(403)
    records = db.session.scalars(db.select(DentalRecord).where(DentalRecord.patient_id == patient.id, DentalRecord.deleted_at.is_(None)).order_by(DentalRecord.visit_at.desc())).all()
    return render_template("dentistry/patient_record.html", patient=patient, records=records)


@dentistry_bp.route("/patients/<patient_id>/dentistry", methods=["GET", "POST"])
@login_required
def patient_dentistry(patient_id):
    patient = _patient(patient_id)
    if current_user.has_role("Patient") and patient.user_id != current_user.id:
        abort(403)
    if not _can_manage_dentistry():
        abort(403)
    if request.method == "POST":
        record = create_dental_record(
            patient,
            actor=current_user,
            visit_at=datetime.utcnow(),
            chief_complaint=request.form.get("chief_complaint"),
            dental_history=request.form.get("dental_history"),
            oral_hygiene_history=request.form.get("oral_hygiene_history"),
            allergies=request.form.getlist("allergies"),
            medical_alerts=request.form.getlist("medical_alerts"),
            dental_complaints=request.form.get("dental_complaints"),
            dental_diagnosis=request.form.get("dental_diagnosis"),
            treatment_plan=request.form.get("treatment_plan"),
            examination=request.form.get("examination"),
        )
        flash("Dental record created.", "success")
        return redirect(url_for("dentistry.patient_records", patient_id=patient.id))
    return render_template("dentistry/patient_record.html", patient=patient, records=db.session.scalars(db.select(DentalRecord).where(DentalRecord.patient_id == patient.id, DentalRecord.deleted_at.is_(None)).order_by(DentalRecord.visit_at.desc())).all())


@dentistry_bp.route("/<record_id>/chart", methods=["GET", "POST"])
@login_required
def dental_chart(record_id):
    record = _record(record_id)
    if not _can_view_record(record):
        abort(403)
    if request.method == "POST" and not _can_manage_dentistry():
        abort(403)
    if request.method == "POST":
        update_dental_chart(
            record,
            actor=current_user,
            tooth_number=request.form.get("tooth_number", "18"),
            condition=request.form.get("condition", "Healthy"),
            caries=request.form.get("caries"),
            missing_teeth=request.form.get("missing_teeth") == "on",
            filled_teeth=request.form.get("filled_teeth") == "on",
            crown_bridge=request.form.get("crown_bridge") == "on",
            implant=request.form.get("implant") == "on",
            root_canal=request.form.get("root_canal") == "on",
            mobility=request.form.get("mobility"),
            periodontal_notes=request.form.get("periodontal_notes"),
            notes=request.form.get("notes"),
        )
        flash("Dental chart updated.", "success")
        return redirect(url_for("dentistry.dental_chart", record_id=record.id))
    return render_template("dentistry/dental_chart.html", record=record, timeline=build_dental_timeline(record))


@dentistry_bp.route("/<record_id>/procedures/create", methods=["GET", "POST"])
@login_required
def procedure_create(record_id):
    record = _record(record_id)
    if not _can_view_record(record):
        abort(403)
    if not _can_manage_dentistry():
        abort(403)
    if request.method == "POST":
        add_dental_procedure(
            record,
            actor=current_user,
            procedure_name=request.form.get("procedure_name"),
            tooth_number=request.form.get("tooth_number"),
            diagnosis=request.form.get("diagnosis"),
            treatment_details=request.form.get("treatment_details"),
            materials_used=request.form.getlist("materials_used"),
            dentist_notes=request.form.get("dentist_notes"),
            performed_at=datetime.utcnow(),
            follow_up_date=request.form.get("follow_up_date"),
            cost_placeholder=float(request.form.get("cost_placeholder") or 0),
        )
        flash("Dental procedure created.", "success")
        return redirect(url_for("dentistry.dental_chart", record_id=record.id))
    return render_template("dentistry/procedure_form.html", record=record)


@dentistry_bp.route("/<record_id>/orthodontic-case/create", methods=["GET", "POST"])
@login_required
def orthodontic_case_create(record_id):
    record = _record(record_id)
    if not _can_view_record(record):
        abort(403)
    if not _can_manage_dentistry():
        abort(403)
    if request.method == "POST":
        create_orthodontic_case(
            record.patient,
            actor=current_user,
            dental_record=record,
            diagnosis=request.form.get("diagnosis"),
            malocclusion_class=request.form.get("malocclusion_class"),
            appliance_type=request.form.get("appliance_type"),
            treatment_plan=request.form.get("treatment_plan"),
            progress_notes=request.form.get("progress_notes"),
            start_date=request.form.get("start_date"),
            expected_end_date=request.form.get("expected_end_date"),
        )
        flash("Orthodontic case created.", "success")
        return redirect(url_for("dentistry.dental_chart", record_id=record.id))
    return render_template("dentistry/orthodontic_case.html", record=record)


@dentistry_bp.route("/<record_id>/images/upload", methods=["GET", "POST"])
@login_required
def image_upload(record_id):
    record = _record(record_id)
    if not _can_view_record(record):
        abort(403)
    if not _can_manage_dentistry():
        abort(403)
    if request.method == "POST":
        file_storage = request.files.get("image")
        if file_storage and file_storage.filename:
            upload_dental_image(
                record,
                actor=current_user,
                file_storage=file_storage,
                image_type=request.form.get("image_type", "intraoral"),
                tooth_number=request.form.get("tooth_number"),
                description=request.form.get("description"),
            )
            flash("Dental image uploaded.", "success")
            return redirect(url_for("dentistry.dental_chart", record_id=record.id))
    return render_template("dentistry/image_upload.html", record=record)

