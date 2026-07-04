# Rehabilitation Module

## Overview

The Rehabilitation Module is Phase 12 of the Intelligent Health Information System (iHIS).

It supports physical therapy and rehabilitation workflows integrated with the central EMR.

The module covers:

- Rehabilitation patient records
- Initial assessments
- Therapy plans
- Therapy sessions
- Exercise library
- Progress tracking
- EMR integration
- Reports dashboard
- Permissions
- Validation rules
- Final testing and freeze checklist

---

## Phase Scope

Phase 12 includes the following sprints:

1. Sprint 12.1 — Database & Models
2. Sprint 12.2 — Business Services
3. Sprint 12.3 — Forms & Routes
4. Sprint 12.4 — User Interface
5. Sprint 12.5 — EMR Integration
6. Sprint 12.6 — Reports
7. Sprint 12.7 — Permissions & Validation
8. Sprint 12.8 — Testing, Documentation & Freeze

The module was designed to be practical, clinical, and EMR-integrated.

Advanced wearable/device integration, video streaming, and billing are not included in Phase 12.

---

## Main Workflow

Typical rehabilitation workflow:

1. Open patient profile.
2. Open Rehabilitation from the patient page or EMR.
3. Create a rehabilitation record.
4. Add initial assessment.
5. Create therapy plan.
6. Add therapy sessions.
7. Track pain and functional progress.
8. Review progress report.
9. Review reports dashboard.
10. Continue follow-up until completion or discharge.

---

## Data Models

### RehabilitationRecord

Represents the main rehabilitation case linked to a patient.

Main fields:

- Patient
- Visit
- Doctor
- Referral source
- Chief complaint
- Functional limitation
- Pain score
- Mobility status
- Rehabilitation diagnosis
- Therapy goals
- Status

Common statuses:

- active
- completed
- closed
- discharged

Locked statuses:

- completed
- closed
- discharged

Locked records cannot be modified through the service layer.

---

### RehabilitationAssessment

Represents the initial or follow-up rehabilitation assessment.

Main fields:

- Rehabilitation record
- Assessment date
- Physical examination
- Range of motion
- Muscle power
- Balance assessment
- Gait assessment
- Neurological findings
- Red flags
- Functional score
- Assessment summary

Validation:

- Assessment date is required.
- Functional score must be between 0 and 100.
- Assessment cannot be added to a locked rehabilitation record.

---

### TherapyPlan

Represents the treatment plan for the rehabilitation case.

Main fields:

- Patient
- Therapist
- Rehabilitation record
- Assessment
- Plan name
- Start date
- End date
- Goals
- Interventions
- Frequency
- Duration
- Modalities
- Exercise program
- Home program
- Review date
- Discharge criteria
- Active status
- Status

Validation:

- Rehabilitation record is required.
- Patient is required.
- Therapist is required.
- Start date is required.
- Goals are required.
- Therapy plan patient must match the rehabilitation record patient.
- Therapy plan cannot be created or updated for a locked record.

---

### TherapySession

Represents a physical therapy session.

Main fields:

- Therapy plan
- Patient
- Therapist
- Therapist user
- Scheduled start
- Session date
- Duration minutes
- Session type
- Interventions
- Response
- Status
- Pain before
- Pain after
- Modalities used
- Exercises performed
- Progress notes
- Patient tolerance
- Next session plan

Validation:

- Therapy plan is required.
- Patient is required.
- Therapist is required.
- Scheduled start is required.
- Pain before must be between 0 and 10.
- Pain after must be between 0 and 10.
- Therapy session patient must match the therapy plan patient.
- Session cannot be added through a plan linked to a locked rehabilitation record.

---

### ExerciseLibrary

Stores reusable rehabilitation exercises.

Main fields:

- Exercise name
- Code
- Category
- Target region
- Indication
- Contraindications
- Instructions
- Image path
- Video path
- Repetitions
- Sets
- Frequency
- Media placeholder
- Active status

Validation:

- Exercise name is required.
- Category is required.
- Instructions are required.

---

## Service Layer

Main service file:

```text
services/rehabilitation_service.py
```

Main functions:

```text
create_rehabilitation_record()
update_rehabilitation_record()
get_patient_rehabilitation_records()
get_rehabilitation_record()

create_initial_assessment()
update_initial_assessment()

create_therapy_plan()
update_therapy_plan()
activate_therapy_plan()
deactivate_therapy_plan()

add_therapy_session()
update_therapy_session()
complete_therapy_session()
calculate_pain_change()
get_plan_sessions()

create_exercise()
update_exercise()

build_rehabilitation_progress()
build_patient_rehabilitation_summary()

build_patient_progress_report()
build_therapist_workload_report()
build_rehabilitation_report_summary()
```

---

## Business Validation

Implemented validation rules:

```text
patient_id is required for rehabilitation records.
pain_score must be between 0 and 10.
pain_before must be between 0 and 10.
pain_after must be between 0 and 10.
functional_score must be between 0 and 100.
rehabilitation_record_id is required for assessments and therapy plans.
therapy_plan_id is required for sessions.
therapy plan patient must match rehabilitation record patient.
therapy session patient must match therapy plan patient.
completed / closed / discharged records are locked.
locked records cannot receive new assessments.
locked records cannot receive new therapy plans.
sessions cannot be added through plans attached to locked records.
```

---

## Record Locking

The following statuses are treated as locked:

```text
completed
closed
discharged
```

Locked records cannot be modified through the service layer.

Blocked actions on locked records:

- Update rehabilitation record
- Create assessment
- Update assessment
- Create therapy plan
- Update therapy plan
- Add therapy session through linked plan

This protects finalized rehabilitation records from accidental clinical changes.

---

## Routes

Main route file:

```text
routes/rehabilitation_routes.py
```

Routes:

```text
/rehabilitation
/rehabilitation/reports

/rehabilitation/patients/<patient_id>
/rehabilitation/patients/<patient_id>/rehabilitation
/rehabilitation/patients/<patient_id>/create

/rehabilitation/<record_id>
/rehabilitation/<record_id>/edit
/rehabilitation/<record_id>/assessment/create
/rehabilitation/<record_id>/therapy-plan/create
/rehabilitation/<record_id>/sessions/create
/rehabilitation/<record_id>/progress

/rehabilitation/therapy-plans/<plan_id>
/rehabilitation/therapy-plans/<plan_id>/edit
/rehabilitation/therapy-plans/<plan_id>/sessions/create

/rehabilitation/exercises
/rehabilitation/exercises/create
/rehabilitation/exercises/<exercise_id>/edit
```

---

## Templates

Main templates:

```text
templates/rehabilitation/dashboard.html
templates/rehabilitation/patient_record.html
templates/rehabilitation/assessment_form.html
templates/rehabilitation/therapy_plan_form.html
templates/rehabilitation/session_form.html
templates/rehabilitation/exercise_library.html
templates/rehabilitation/exercise_form.html
templates/rehabilitation/progress.html
templates/rehabilitation/reports.html
```

---

## Forms

Main form file:

```text
rehabilitation/forms.py
```

Forms:

- RehabilitationRecordForm
- RehabilitationAssessmentForm
- TherapyPlanForm
- TherapySessionForm
- ExerciseLibraryForm

---

## Dashboard

Route:

```text
/rehabilitation
```

Dashboard shows:

- Rehabilitation records count
- Active therapy plans count
- Exercise library count
- Recent rehabilitation records
- Link to reports
- Link to exercise library

---

## Reports

Route:

```text
/rehabilitation/reports
```

Reports dashboard includes:

- Total rehabilitation records
- Active records
- Completed records
- Active therapy plans
- Total therapy sessions
- Completed therapy sessions
- Average latest pain score
- Average functional score
- Records needing review
- Patient progress report
- Therapist workload report

Current reports are HTML-based and browser-printable.

PDF generation is not implemented in Phase 12.

Future reports may include:

- Initial assessment PDF
- Therapy plan PDF
- Progress report PDF
- Discharge summary
- Exercise sheet

---

## Progress Tracking

Route:

```text
/rehabilitation/<record_id>/progress
```

Progress summary includes:

- Total plans
- Active plans
- Total sessions
- Completed sessions
- Latest pain score
- Latest functional score
- Latest assessment

Pain progress is currently based on completed therapy sessions and latest pain-after value.

Functional progress is currently based on latest assessment functional score.

---

## EMR Integration

Rehabilitation is integrated with the central EMR.

Integration points:

- Patient profile quick action
- EMR dashboard rehabilitation summary
- EMR timeline rehabilitation events
- Visit detail rehabilitation action

Timeline event types:

```text
rehabilitation_record
rehabilitation_assessment
therapy_plan
therapy_session
```

The patient timeline can show rehabilitation activity alongside visits, labs, radiology, attachments, prescriptions, and women’s health events.

---

## Permissions

### Super Admin

Full access.

Can:

- View dashboard
- View reports
- Create records
- Edit records
- Create assessments
- Create therapy plans
- Add sessions
- Manage exercise library
- View progress

---

### Admin

Full administrative access.

Can:

- View dashboard
- View reports
- Create records
- Edit records
- Create assessments
- Create therapy plans
- Add sessions
- Manage exercise library
- View progress

---

### Rehabilitation Specialist

Clinical management access.

Can:

- View dashboard
- Create rehabilitation records
- Edit rehabilitation records
- Create assessments
- Create therapy plans
- Add therapy sessions
- Manage exercise library
- View reports
- View progress

---

### Doctor

View-focused clinical access.

Can:

- View rehabilitation records
- View progress
- View reports

Doctor management access is intentionally limited unless expanded later.

---

### Receptionist

Receptionist is blocked from rehabilitation clinical records and reports.

Current rule:

- Cannot open rehabilitation dashboard.
- Cannot open reports.
- Cannot edit rehabilitation records.

Future scope:

- Receptionist may book rehabilitation appointments only.

---

### Nurse

Nurse access is not expanded in Phase 12.

Future scope:

- Nurses may view assigned rehabilitation care notes.
- Nurses may add care team notes if required.

---

### Patient

Patient access is limited.

Current rule:

- Patient cannot manage or edit rehabilitation data.
- Patient should only view permitted own rehabilitation records if allowed by route logic.

Future scope:

- Patient-approved home program portal.
- Patient exercise sheet view.
- Patient progress summary view.

---

## Audit Logging

Audit logging is planned for formal production hardening.

Expected future audit events:

```text
rehab.record_created
rehab.record_updated
rehab.assessment_created
rehab.assessment_updated
rehab.therapy_plan_created
rehab.therapy_plan_updated
rehab.session_created
rehab.session_updated
rehab.exercise_created
rehab.exercise_updated
rehab.progress_viewed
rehab.report_viewed
```

Current Phase 12 documentation records the audit requirements.

Full audit event implementation should be reviewed in a future security hardening sprint.

---

## Testing

Main test file:

```text
tests/test_rehabilitation_models.py
```

Coverage includes:

- Model creation
- Relationships
- Nullable relationships
- Service creation
- Service update
- Pain score validation
- Functional score validation
- Patient ownership validation
- Therapy plan patient mismatch rejection
- Therapy session patient mismatch rejection
- Record locking
- Exercise creation/update
- Progress summary
- Patient summary
- EMR timeline integration
- Reports summary
- Patient progress report
- Therapist workload report
- Route registration
- Permission tests

---

## Verification Commands

Sprint verification:

```powershell
python -m pytest tests/test_rehabilitation_models.py -q
python -m pytest -q
python -m flask --app app db check
git status
git diff --stat
```

Final freeze verification:

```powershell
python -m pytest -q

python -m flask --app app db upgrade
python -m flask --app app db downgrade
python -m flask --app app db upgrade
python -m flask --app app db check

git status
git diff --stat
```

---

## Manual Testing Checklist

Use this checklist before Phase 12 freeze:

```text
Open /rehabilitation as Admin.
Confirm dashboard loads.
Confirm Reports button opens /rehabilitation/reports.
Confirm reports cards display.
Confirm patient progress table displays.
Confirm therapist workload table displays.
Open patient profile.
Confirm Rehabilitation quick action appears.
Open EMR dashboard.
Confirm rehabilitation summary appears.
Open EMR timeline.
Confirm rehabilitation events appear.
Open visit detail.
Confirm Rehabilitation action appears.
Create rehabilitation record.
Create assessment.
Create therapy plan.
Create therapy session.
Complete therapy session.
Open progress page.
Confirm progress values update.
Try invalid pain score.
Confirm validation blocks it.
Try invalid functional score.
Confirm validation blocks it.
Try cross-patient therapy plan.
Confirm validation blocks it.
Try cross-patient therapy session.
Confirm validation blocks it.
Mark record completed.
Confirm service layer blocks updates/new assessment/new plan.
Login as Receptionist.
Confirm dashboard/reports are blocked.
Login as Doctor.
Confirm reports/record view are allowed.
Login as Patient.
Confirm other patient record is blocked.
Run full tests.
Run migration checks.
Review git status.
```

---

## Freeze Review Checklist

Phase 12 can be frozen only when:

```text
Models verified.
Migrations verified.
Services verified.
Forms verified.
Routes verified.
Templates verified.
Reports verified.
EMR integration verified.
Permissions verified.
Validation verified.
Tests pass.
Full test suite passes.
db upgrade passes.
db downgrade passes.
db upgrade again passes.
db check clean.
Documentation exists.
No unrelated file changes.
Git status reviewed.
Commit prepared.
```

---

## Known Limitations

Current limitations:

- No PDF generation.
- No wearable/device integration.
- No video exercise streaming.
- No billing integration.
- No digital signature workflow.
- Audit logging is documented but not fully implemented.
- Fine-grained therapist ownership can be improved later.
- Patient home program portal is future scope.

---

## Future Enhancements

Recommended future improvements:

- PDF reports.
- Printable assessment sheets.
- Printable therapy plan sheets.
- Printable exercise sheets.
- Discharge summary.
- Therapist schedule dashboard.
- Rehabilitation appointment booking.
- Fine-grained therapist ownership rules.
- Full audit logging.
- Digital signatures.
- Patient-approved home program.
- Outcome measure scoring templates.
- Wearable/device integration.
- Mobile-friendly patient exercise view.
- AI-assisted progress summarization.

---

## Phase 12 Status

Current status:

```text
Sprint 12.1 — Database & Models: Frozen
Sprint 12.2 — Business Services: Frozen
Sprint 12.3 — Forms & Routes: Frozen
Sprint 12.4 — User Interface: Frozen
Sprint 12.5 — EMR Integration: Frozen
Sprint 12.6 — Reports: Completed
Sprint 12.7 — Permissions & Validation: In Progress
Sprint 12.8 — Testing & Freeze: In Progress
```
