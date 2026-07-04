"""Simple Nursing module routes."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from auth.decorators import login_required
from extensions import db
from models import MedicalRecord, Patient
from nursing.forms import (
    MedicationAdministrationForm,
    NursingCarePlanForm,
    SimpleNursingNoteForm,
    SimpleVitalSignForm,
)
from services.nursing_service import (
    NursingServiceError,
    administer_medication,
    build_nursing_dashboard,
    build_simple_nursing_alerts,
    create_care_plan,
    create_nursing_note,
    get_assigned_patients,
    record_vital_signs,
)


nursing_bp = Blueprint("nursing", __name__, url_prefix="/nursing")


def _can_view_nursing():
    return current_user.has_role(
        "Super Admin",
        "Admin",
        "Nurse",
        "Doctor",
        "Women’s Health Doctor",
    )


def _can_manage_nursing():
    return current_user.has_role(
        "Super Admin",
        "Admin",
        "Nurse",
        "Doctor",
        "Women’s Health Doctor",
    )


def _patient(patient_id):
    return db.get_or_404(Patient, patient_id)


def _blank_choice(label="Not linked"):
    return [("", label)]


def _patient_choices():
    patients = db.session.scalars(
        db.select(Patient)
        .where(Patient.deleted_at.is_(None))
        .order_by(Patient.last_name, Patient.first_name)
    ).all()

    return [
        (
            patient.id,
            f"{patient.medical_record_number} · {patient.first_name} {patient.last_name}",
        )
        for patient in patients
    ]


def _visit_choices(patient_id=None):
    statement = db.select(MedicalRecord).where(MedicalRecord.deleted_at.is_(None))

    if patient_id:
        statement = statement.where(MedicalRecord.patient_id == patient_id)

    visits = db.session.scalars(
        statement.order_by(MedicalRecord.encounter_at.desc())
    ).all()

    return _blank_choice("No linked visit") + [
        (
            visit.id,
            f"{visit.record_number} · {visit.encounter_type} · {visit.encounter_at}",
        )
        for visit in visits
    ]


def _prescription_item_choices():
    # Keep simple for Phase 13. Medication can be entered manually.
    return _blank_choice("No linked prescription item")


def _empty_to_none(value):
    return value or None


@nursing_bp.get("")
@nursing_bp.get("/")
@login_required
def dashboard():
    if not _can_view_nursing():
        abort(403)

    dashboard_data = build_nursing_dashboard(current_user)

    return render_template(
        "nursing/dashboard.html",
        dashboard=dashboard_data,
    )


@nursing_bp.get("/patients")
@login_required
def patients():
    if not _can_view_nursing():
        abort(403)

    return render_template(
        "nursing/patients.html",
        patients=get_assigned_patients(current_user),
    )


@nursing_bp.route("/patients/<patient_id>/vitals/create", methods=["GET", "POST"])
@login_required
def create_vitals(patient_id):
    if not _can_manage_nursing():
        abort(403)

    patient = _patient(patient_id)
    form = SimpleVitalSignForm()
    form.medical_record_id.choices = _visit_choices(patient.id)

    if form.validate_on_submit():
        try:
            record_vital_signs(
                actor=current_user,
                patient_id=patient.id,
                medical_record_id=_empty_to_none(form.medical_record_id.data),
                temperature_c=form.temperature_c.data,
                pulse_bpm=form.pulse_bpm.data,
                respiratory_rate=form.respiratory_rate.data,
                systolic_bp=form.systolic_bp.data,
                diastolic_bp=form.diastolic_bp.data,
                oxygen_saturation=form.oxygen_saturation.data,
                weight_kg=form.weight_kg.data,
                height_cm=form.height_cm.data,
                pain_score=form.pain_score.data,
            )
            flash("Vital signs recorded.", "success")
            return redirect(url_for("nursing.dashboard"))
        except (NursingServiceError, PermissionError) as exc:
            flash(str(exc), "danger")

    return render_template(
        "nursing/vitals_form.html",
        patient=patient,
        form=form,
    )


@nursing_bp.route("/patients/<patient_id>/nursing-notes/create", methods=["GET", "POST"])
@login_required
def create_note(patient_id):
    if not _can_manage_nursing():
        abort(403)

    patient = _patient(patient_id)
    form = SimpleNursingNoteForm()
    form.medical_record_id.choices = _visit_choices(patient.id)

    if form.validate_on_submit():
        try:
            create_nursing_note(
                actor=current_user,
                patient_id=patient.id,
                medical_record_id=_empty_to_none(form.medical_record_id.data),
                note_type=form.note_type.data,
                subjective_note=form.subjective_note.data,
                objective_note=form.objective_note.data,
                nursing_assessment=form.nursing_assessment.data,
                nursing_intervention=form.nursing_intervention.data,
                response_to_care=form.response_to_care.data,
                follow_up_recommendation=form.follow_up_recommendation.data,
            )
            flash("Nursing note created.", "success")
            return redirect(url_for("nursing.dashboard"))
        except (NursingServiceError, PermissionError) as exc:
            flash(str(exc), "danger")

    return render_template(
        "nursing/nursing_note_form.html",
        patient=patient,
        form=form,
    )


@nursing_bp.route("/medication-administration", methods=["GET", "POST"])
@login_required
def medication_administration():
    if not _can_manage_nursing():
        abort(403)

    form = MedicationAdministrationForm()
    form.patient_id.choices = _patient_choices()
    selected_patient_id = request.form.get("patient_id") or request.args.get("patient_id")
    form.medical_record_id.choices = _visit_choices(selected_patient_id)
    form.prescription_item_id.choices = _prescription_item_choices()

    if form.validate_on_submit():
        try:
            administer_medication(
                actor=current_user,
                patient_id=form.patient_id.data,
                medical_record_id=_empty_to_none(form.medical_record_id.data),
                prescription_item_id=_empty_to_none(form.prescription_item_id.data),
                medication_name=form.medication_name.data,
                dose=form.dose.data,
                scheduled_time=form.scheduled_time.data,
                given_at=form.given_at.data,
                status=form.status.data,
                missed_reason=form.missed_reason.data,
                patient_reaction=form.patient_reaction.data,
                notes=form.notes.data,
            )
            flash("Medication administration saved.", "success")
            return redirect(url_for("nursing.dashboard"))
        except (NursingServiceError, PermissionError) as exc:
            flash(str(exc), "danger")

    return render_template(
        "nursing/medication_administration.html",
        form=form,
    )


@nursing_bp.get("/care-plans")
@login_required
def care_plans():
    if not _can_view_nursing():
        abort(403)

    from models import NursingCarePlan

    plans = db.session.scalars(
        db.select(NursingCarePlan)
        .where(NursingCarePlan.deleted_at.is_(None))
        .order_by(NursingCarePlan.created_at.desc())
    ).all()

    return render_template(
        "nursing/care_plan_form.html",
        form=None,
        plans=plans,
    )


@nursing_bp.route("/care-plans/create", methods=["GET", "POST"])
@login_required
def create_care_plan_route():
    if not _can_manage_nursing():
        abort(403)

    form = NursingCarePlanForm()
    form.patient_id.choices = _patient_choices()
    selected_patient_id = request.form.get("patient_id") or request.args.get("patient_id")
    form.medical_record_id.choices = _visit_choices(selected_patient_id)

    if form.validate_on_submit():
        try:
            create_care_plan(
                actor=current_user,
                patient_id=form.patient_id.data,
                medical_record_id=_empty_to_none(form.medical_record_id.data),
                nursing_diagnosis=form.nursing_diagnosis.data,
                goals=form.goals.data,
                interventions=form.interventions.data,
                evaluation=form.evaluation.data,
                status=form.status.data,
            )
            flash("Nursing care plan created.", "success")
            return redirect(url_for("nursing.care_plans"))
        except (NursingServiceError, PermissionError) as exc:
            flash(str(exc), "danger")

    return render_template(
        "nursing/care_plan_form.html",
        form=form,
        plans=None,
    )


@nursing_bp.get("/alerts")
@login_required
def alerts():
    if not _can_view_nursing():
        abort(403)

    return render_template(
        "nursing/alerts.html",
        alerts=build_simple_nursing_alerts(current_user),
    )