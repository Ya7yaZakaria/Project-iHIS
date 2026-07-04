"""Rehabilitation module routes and views."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.orm import selectinload

from auth.decorators import login_required
from extensions import db
from models import (
    ExerciseLibrary,
    MedicalRecord,
    Patient,
    PhysicalTherapist,
    RehabilitationRecord,
    TherapyPlan,
    User,
)
from rehabilitation.forms import (
    ExerciseLibraryForm,
    RehabilitationAssessmentForm,
    RehabilitationRecordForm,
    TherapyPlanForm,
    TherapySessionForm,
)
from services.rehabilitation_service import (
    RehabilitationServiceError,
    add_therapy_session,
    build_rehabilitation_progress,
    build_rehabilitation_report_summary,
    create_exercise,
    create_initial_assessment,
    create_rehabilitation_record,
    create_therapy_plan,
    get_patient_rehabilitation_records,
    get_plan_sessions,
    update_exercise,
    update_rehabilitation_record,
    update_therapy_plan,
)


rehabilitation_bp = Blueprint(
    "rehabilitation",
    __name__,
    url_prefix="/rehabilitation",
)


def _patient(patient_id):
    return db.get_or_404(Patient, patient_id)


def _record(record_id):
    return db.get_or_404(RehabilitationRecord, record_id)


def _therapy_plan(plan_id):
    return db.get_or_404(TherapyPlan, plan_id)


def _exercise(exercise_id):
    return db.get_or_404(ExerciseLibrary, exercise_id)


def _can_manage_rehabilitation():
    return current_user.has_role(
        "Super Admin",
        "Admin",
        "Rehabilitation Specialist",
    )


def _can_view_rehabilitation_record(record):
    if current_user.has_role(
        "Super Admin",
        "Admin",
        "Rehabilitation Specialist",
        "Doctor",
    ):
        return True

    if current_user.has_role("Patient"):
        patient = db.session.scalar(
            db.select(Patient).where(Patient.user_id == current_user.id)
        )
        return bool(
            patient
            and patient.id == record.patient_id
            and record.status in {"active", "completed"}
        )

    return False


def _can_view_patient_rehabilitation(patient):
    if current_user.has_role(
        "Super Admin",
        "Admin",
        "Rehabilitation Specialist",
        "Doctor",
    ):
        return True

    if current_user.has_role("Patient"):
        return patient.user_id == current_user.id

    return False

def _can_view_rehabilitation_reports():
    return current_user.has_role(
        "Super Admin",
        "Admin",
        "Rehabilitation Specialist",
        "Doctor",
    )

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
            f"{patient.medical_record_number or patient.id} · "
            f"{patient.first_name} {patient.last_name}",
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
            f"{visit.record_number or visit.id} · "
            f"{visit.encounter_type or 'visit'} · "
            f"{visit.encounter_at or ''}",
        )
        for visit in visits
    ]


def _doctor_choices():
    users = db.session.scalars(
        db.select(User)
        .where(User.deleted_at.is_(None))
        .order_by(User.last_name, User.first_name)
    ).all()

    doctor_users = [
        user
        for user in users
        if user.has_role("Doctor")
        or user.has_role("Super Admin")
        or user.has_role("Admin")
    ]

    return _blank_choice("No linked doctor") + [
        (
            user.id,
            f"{user.first_name or ''} {user.last_name or ''}".strip()
            or user.username,
        )
        for user in doctor_users
    ]


def _therapist_choices():
    therapists = db.session.scalars(
        db.select(PhysicalTherapist)
        .join(PhysicalTherapist.user)
        .where(PhysicalTherapist.deleted_at.is_(None))
        .order_by(User.last_name, User.first_name)
    ).all()

    return [
        (
            therapist.id,
            (
                f"{therapist.user.first_name or ''} "
                f"{therapist.user.last_name or ''}"
            ).strip()
            or therapist.user.username
            or therapist.license_number,
        )
        for therapist in therapists
    ]


def _therapist_user_choices():
    users = db.session.scalars(
        db.select(User)
        .where(User.deleted_at.is_(None))
        .order_by(User.last_name, User.first_name)
    ).all()

    therapist_users = [
        user
        for user in users
        if user.has_role("Rehabilitation Specialist")
        or user.has_role("Admin")
        or user.has_role("Super Admin")
    ]

    return _blank_choice("No linked therapist user") + [
        (
            user.id,
            f"{user.first_name or ''} {user.last_name or ''}".strip()
            or user.username,
        )
        for user in therapist_users
    ]


def _assessment_choices(record):
    return _blank_choice("No linked assessment") + [
        (
            assessment.id,
            f"{assessment.assessment_date} · "
            f"{assessment.assessment_summary or 'Assessment'}",
        )
        for assessment in sorted(
            record.assessments or [],
            key=lambda item: item.assessment_date,
            reverse=True,
        )
    ]


def _set_record_form_choices(form, patient_id=None):
    form.patient_id.choices = _patient_choices()
    form.visit_id.choices = _visit_choices(patient_id)
    form.doctor_id.choices = _doctor_choices()


def _set_therapy_plan_form_choices(form, record):
    form.therapist_id.choices = _therapist_choices()
    form.assessment_id.choices = _assessment_choices(record)


def _set_therapy_session_form_choices(form):
    form.therapist_id.choices = _therapist_choices()
    form.therapist_user_id.choices = _therapist_user_choices()


def _empty_to_none(value):
    return value or None


def _form_data(form, fields):
    return {
        field: _empty_to_none(getattr(form, field).data)
        for field in fields
    }


@rehabilitation_bp.get("")
@rehabilitation_bp.get("/")
@login_required
def index():
    if current_user.has_role("Receptionist"):
        abort(403)

    records = db.session.scalars(
        db.select(RehabilitationRecord)
        .options(
            selectinload(RehabilitationRecord.patient),
            selectinload(RehabilitationRecord.assessments),
            selectinload(RehabilitationRecord.therapy_plans),
        )
        .where(RehabilitationRecord.deleted_at.is_(None))
        .order_by(RehabilitationRecord.created_at.desc())
    ).all()

    active_plans = db.session.scalars(
        db.select(TherapyPlan)
        .where(
            TherapyPlan.deleted_at.is_(None),
            TherapyPlan.active.is_(True),
        )
        .order_by(TherapyPlan.review_date.asc())
    ).all()

    exercises = db.session.scalars(
        db.select(ExerciseLibrary)
        .where(ExerciseLibrary.deleted_at.is_(None))
        .order_by(ExerciseLibrary.name.asc())
        .limit(10)
    ).all()

    return render_template(
        "rehabilitation/dashboard.html",
        records=records,
        active_plans=active_plans,
        exercises=exercises,
    )


@rehabilitation_bp.get("/reports")
@login_required
def reports():
    if not _can_view_rehabilitation_reports():
        abort(403)

    report_summary = build_rehabilitation_report_summary()

    return render_template(
        "rehabilitation/reports.html",
        report_summary=report_summary,
    )


@rehabilitation_bp.get("/patients/<patient_id>")
@rehabilitation_bp.get("/patients/<patient_id>/rehabilitation")
@login_required
def patient_records(patient_id):
    patient = _patient(patient_id)

    if not _can_view_patient_rehabilitation(patient):
        abort(403)

    if current_user.has_role("Receptionist"):
        abort(403)

    records = get_patient_rehabilitation_records(patient.id)

    return render_template(
        "rehabilitation/patient_record.html",
        patient=patient,
        records=records,
        form=RehabilitationRecordForm(),
    )


@rehabilitation_bp.route("/patients/<patient_id>/create", methods=["GET", "POST"])
@login_required
def record_create(patient_id):
    patient = _patient(patient_id)

    if not _can_manage_rehabilitation():
        abort(403)

    form = RehabilitationRecordForm()
    _set_record_form_choices(form, patient.id)
    form.patient_id.data = patient.id

    if form.validate_on_submit():
        try:
            record = create_rehabilitation_record(
                **_form_data(
                    form,
                    (
                        "patient_id",
                        "visit_id",
                        "doctor_id",
                        "referral_source",
                        "chief_complaint",
                        "functional_limitation",
                        "pain_score",
                        "mobility_status",
                        "rehabilitation_diagnosis",
                        "therapy_goals",
                        "status",
                    ),
                )
            )
            flash("Rehabilitation record created.", "success")
            return redirect(
                url_for(
                    "rehabilitation.record_detail",
                    record_id=record.id,
                )
            )
        except RehabilitationServiceError as exc:
            flash(str(exc), "danger")

    return render_template(
        "rehabilitation/patient_record.html",
        patient=patient,
        records=get_patient_rehabilitation_records(patient.id),
        form=form,
    )


@rehabilitation_bp.get("/<record_id>")
@login_required
def record_detail(record_id):
    record = _record(record_id)

    if not _can_view_rehabilitation_record(record):
        abort(403)

    progress = build_rehabilitation_progress(record)

    return render_template(
        "rehabilitation/patient_record.html",
        patient=record.patient,
        record=record,
        records=[record],
        progress=progress,
    )


@rehabilitation_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
def record_edit(record_id):
    record = _record(record_id)

    if not _can_manage_rehabilitation():
        abort(403)

    form = RehabilitationRecordForm(obj=record)
    _set_record_form_choices(form, record.patient_id)

    if request.method == "GET":
        form.patient_id.data = record.patient_id
        form.visit_id.data = record.visit_id or ""
        form.doctor_id.data = record.doctor_id or ""

    if form.validate_on_submit():
        try:
            update_rehabilitation_record(
                record,
                **_form_data(
                    form,
                    (
                        "patient_id",
                        "visit_id",
                        "doctor_id",
                        "referral_source",
                        "chief_complaint",
                        "functional_limitation",
                        "pain_score",
                        "mobility_status",
                        "rehabilitation_diagnosis",
                        "therapy_goals",
                        "status",
                    ),
                ),
            )
            flash("Rehabilitation record updated.", "success")
            return redirect(
                url_for(
                    "rehabilitation.record_detail",
                    record_id=record.id,
                )
            )
        except RehabilitationServiceError as exc:
            flash(str(exc), "danger")

    return render_template(
        "rehabilitation/patient_record.html",
        patient=record.patient,
        record=record,
        records=[record],
        form=form,
    )


@rehabilitation_bp.route(
    "/<record_id>/assessment/create",
    methods=["GET", "POST"],
)
@login_required
def assessment_create(record_id):
    record = _record(record_id)

    if not _can_manage_rehabilitation():
        abort(403)

    form = RehabilitationAssessmentForm()

    if form.validate_on_submit():
        try:
            create_initial_assessment(
                rehabilitation_record_id=record.id,
                **_form_data(
                    form,
                    (
                        "assessment_date",
                        "physical_exam",
                        "range_of_motion",
                        "muscle_power",
                        "balance_assessment",
                        "gait_assessment",
                        "neurological_findings",
                        "red_flags",
                        "functional_score",
                        "assessment_summary",
                    ),
                ),
            )
            flash("Rehabilitation assessment created.", "success")
            return redirect(
                url_for(
                    "rehabilitation.record_detail",
                    record_id=record.id,
                )
            )
        except RehabilitationServiceError as exc:
            flash(str(exc), "danger")

    return render_template(
        "rehabilitation/assessment_form.html",
        record=record,
        form=form,
    )


@rehabilitation_bp.route(
    "/<record_id>/therapy-plan/create",
    methods=["GET", "POST"],
)
@login_required
def therapy_plan_create(record_id):
    record = _record(record_id)

    if not _can_manage_rehabilitation():
        abort(403)

    form = TherapyPlanForm()
    _set_therapy_plan_form_choices(form, record)

    if form.validate_on_submit():
        try:
            plan = create_therapy_plan(
                rehabilitation_record_id=record.id,
                patient_id=record.patient_id,
                **_form_data(
                    form,
                    (
                        "therapist_id",
                        "assessment_id",
                        "plan_name",
                        "start_date",
                        "end_date",
                        "goals",
                        "interventions",
                        "frequency",
                        "duration",
                        "modalities",
                        "exercise_program",
                        "home_program",
                        "review_date",
                        "discharge_criteria",
                        "active",
                        "status",
                    ),
                ),
            )
            flash("Therapy plan created.", "success")
            return redirect(
                url_for(
                    "rehabilitation.therapy_plan_detail",
                    plan_id=plan.id,
                )
            )
        except RehabilitationServiceError as exc:
            flash(str(exc), "danger")

    return render_template(
        "rehabilitation/therapy_plan_form.html",
        record=record,
        form=form,
    )


@rehabilitation_bp.get("/therapy-plans/<plan_id>")
@login_required
def therapy_plan_detail(plan_id):
    plan = _therapy_plan(plan_id)

    if not plan.rehabilitation_record:
        abort(404)

    if not _can_view_rehabilitation_record(plan.rehabilitation_record):
        abort(403)

    sessions = get_plan_sessions(plan.id)

    return render_template(
        "rehabilitation/therapy_plan_form.html",
        record=plan.rehabilitation_record,
        plan=plan,
        sessions=sessions,
    )


@rehabilitation_bp.route(
    "/therapy-plans/<plan_id>/edit",
    methods=["GET", "POST"],
)
@login_required
def therapy_plan_edit(plan_id):
    plan = _therapy_plan(plan_id)

    if not plan.rehabilitation_record:
        abort(404)

    if not _can_manage_rehabilitation():
        abort(403)

    record = plan.rehabilitation_record
    form = TherapyPlanForm(obj=plan)
    _set_therapy_plan_form_choices(form, record)

    if request.method == "GET":
        form.therapist_id.data = plan.therapist_id
        form.assessment_id.data = plan.assessment_id or ""

    if form.validate_on_submit():
        try:
            update_therapy_plan(
                plan,
                **_form_data(
                    form,
                    (
                        "therapist_id",
                        "assessment_id",
                        "plan_name",
                        "start_date",
                        "end_date",
                        "goals",
                        "interventions",
                        "frequency",
                        "duration",
                        "modalities",
                        "exercise_program",
                        "home_program",
                        "review_date",
                        "discharge_criteria",
                        "active",
                        "status",
                    ),
                ),
            )
            flash("Therapy plan updated.", "success")
            return redirect(
                url_for(
                    "rehabilitation.therapy_plan_detail",
                    plan_id=plan.id,
                )
            )
        except RehabilitationServiceError as exc:
            flash(str(exc), "danger")

    return render_template(
        "rehabilitation/therapy_plan_form.html",
        record=record,
        plan=plan,
        form=form,
    )


@rehabilitation_bp.route(
    "/therapy-plans/<plan_id>/sessions/create",
    methods=["GET", "POST"],
)
@rehabilitation_bp.route(
    "/<record_id>/sessions/create",
    methods=["GET", "POST"],
)
@login_required
def session_create(plan_id=None, record_id=None):
    plan = _therapy_plan(plan_id) if plan_id else None
    record = plan.rehabilitation_record if plan else _record(record_id)

    if not _can_manage_rehabilitation():
        abort(403)

    if not record:
        abort(404)

    form = TherapySessionForm()
    _set_therapy_session_form_choices(form)

    if plan and request.method == "GET":
        form.therapist_id.data = plan.therapist_id

    if form.validate_on_submit():
        try:
            selected_plan_id = plan.id if plan else None
            selected_patient_id = plan.patient_id if plan else record.patient_id

            add_therapy_session(
                therapy_plan_id=selected_plan_id,
                patient_id=selected_patient_id,
                **_form_data(
                    form,
                    (
                        "therapist_id",
                        "therapist_user_id",
                        "scheduled_start",
                        "session_date",
                        "duration_minutes",
                        "session_type",
                        "interventions",
                        "response",
                        "status",
                        "pain_before",
                        "pain_after",
                        "modalities_used",
                        "exercises_performed",
                        "progress_notes",
                        "patient_tolerance",
                        "next_session_plan",
                    ),
                ),
            )
            flash("Therapy session created.", "success")

            if plan:
                return redirect(
                    url_for(
                        "rehabilitation.therapy_plan_detail",
                        plan_id=plan.id,
                    )
                )

            return redirect(
                url_for(
                    "rehabilitation.record_detail",
                    record_id=record.id,
                )
            )
        except RehabilitationServiceError as exc:
            flash(str(exc), "danger")

    return render_template(
        "rehabilitation/session_form.html",
        record=record,
        plan=plan,
        form=form,
    )


@rehabilitation_bp.get("/exercises")
@login_required
def exercises():
    if current_user.has_role("Receptionist"):
        abort(403)

    search = request.args.get("search", "").strip()

    statement = db.select(ExerciseLibrary).where(
        ExerciseLibrary.deleted_at.is_(None)
    )

    if search:
        term = f"%{search}%"
        statement = statement.where(
            db.or_(
                ExerciseLibrary.name.ilike(term),
                ExerciseLibrary.category.ilike(term),
                ExerciseLibrary.target_region.ilike(term),
            )
        )

    items = db.session.scalars(
        statement.order_by(
            ExerciseLibrary.category.asc(),
            ExerciseLibrary.name.asc(),
        )
    ).all()

    return render_template(
        "rehabilitation/exercise_library.html",
        exercises=items,
        search=search,
    )


@rehabilitation_bp.route("/exercises/create", methods=["GET", "POST"])
@login_required
def exercise_create():
    if not _can_manage_rehabilitation():
        abort(403)

    form = ExerciseLibraryForm()

    if form.validate_on_submit():
        try:
            exercise = create_exercise(
                **_form_data(
                    form,
                    (
                        "code",
                        "exercise_name",
                        "category",
                        "target_region",
                        "indication",
                        "contraindications",
                        "instructions",
                        "image_path",
                        "video_path",
                        "repetitions",
                        "sets",
                        "frequency",
                        "media_placeholder",
                        "active",
                    ),
                )
            )
            flash("Exercise created.", "success")
            return redirect(
                url_for(
                    "rehabilitation.exercise_edit",
                    exercise_id=exercise.id,
                )
            )
        except RehabilitationServiceError as exc:
            flash(str(exc), "danger")

    return render_template(
        "rehabilitation/exercise_form.html",
        form=form,
        exercise=None,
    )


@rehabilitation_bp.route(
    "/exercises/<exercise_id>/edit",
    methods=["GET", "POST"],
)
@login_required
def exercise_edit(exercise_id):
    exercise = _exercise(exercise_id)

    if not _can_manage_rehabilitation():
        abort(403)

    form = ExerciseLibraryForm(obj=exercise)

    if request.method == "GET":
        form.exercise_name.data = exercise.name

    if form.validate_on_submit():
        try:
            update_exercise(
                exercise,
                **_form_data(
                    form,
                    (
                        "code",
                        "exercise_name",
                        "category",
                        "target_region",
                        "indication",
                        "contraindications",
                        "instructions",
                        "image_path",
                        "video_path",
                        "repetitions",
                        "sets",
                        "frequency",
                        "media_placeholder",
                        "active",
                    ),
                ),
            )
            flash("Exercise updated.", "success")
            return redirect(
                url_for(
                    "rehabilitation.exercises",
                )
            )
        except RehabilitationServiceError as exc:
            flash(str(exc), "danger")

    return render_template(
        "rehabilitation/exercise_form.html",
        form=form,
        exercise=exercise,
    )


@rehabilitation_bp.get("/<record_id>/progress")
@login_required
def progress(record_id):
    record = _record(record_id)

    if not _can_view_rehabilitation_record(record):
        abort(403)

    return render_template(
        "rehabilitation/progress.html",
        record=record,
        progress=build_rehabilitation_progress(record),
    )