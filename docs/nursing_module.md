# Nursing Module

## Scope

Phase 13 implements a simple EMR-integrated Nursing Module.

It intentionally avoids full inpatient ward management, ICU monitoring, device integration, barcode medication administration, and complex nurse assignment.

## Architecture

The module reuses existing EMR models:

- `VitalSign`
- `NursingNote`

It adds only two nursing-specific models:

- `MedicationAdministration`
- `NursingCarePlan`

## Workflow

Nurse can:

1. Open Nursing Dashboard.
2. View today/recent patients.
3. Record vital signs.
4. Add nursing notes.
5. Record medication administration.
6. Create nursing care plans.
7. Review simple computed alerts.

Doctor can view nursing records through EMR/nursing views.

Admin and Super Admin can access all nursing workflows.

## Vital Signs

Vital signs are stored using the existing EMR `VitalSign` model.

Supported fields:

- Systolic BP
- Diastolic BP
- Pulse
- Temperature
- Respiratory rate
- SpO2
- Weight
- Height
- Pain score

BMI is calculated in service using:

```text
BMI = weight_kg / height_m²

Nursing Notes

Nursing notes are stored using the existing EMR NursingNote model.

The module writes structured content into the existing note field:

Subjective
Objective
Nursing assessment
Nursing intervention
Response to care
Follow-up recommendation
Medication Administration

Medication administration stores:

Patient
Optional visit / medical record
Optional prescription item
Medication name
Dose
Scheduled time
Given time
Status
Given by nurse
Missed reason
Patient reaction
Notes

Statuses:

Given
Missed
Held
Refused

If the medication is not given, a reason is required.

Care Plans

Care plans store:

Patient
Optional visit / medical record
Nursing diagnosis
Goals
Interventions
Evaluation
Status

Statuses:

Active
Improved
Completed
Cancelled
Alerts

Alerts are computed, not stored.

Current simple alerts:

SpO2 below 92
Temperature 38°C or above
Pain score 8 or above
Missed / held / refused medication
Permissions

Nurse:

Add vitals
Add nursing notes
Record medication administration
Create care plans

Doctor:

View nursing data

Admin / Super Admin:

Full access

Receptionist:

No nursing management access
Audit Logging

The service writes audit entries for:

Vitals recorded
Nursing note created
Medication administration recorded
Care plan created