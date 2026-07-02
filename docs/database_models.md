# iHIS Database Models

## Design conventions

Every domain entity uses an application-generated UUID4 stored as `String(36)`, portable SQLAlchemy types, timestamps, an active flag, soft deletion, and a nullable tenant identifier. Association tables use composite foreign keys. Status values are strings so workflows can evolve without database-specific enum migrations.

Clinical records are retained when users or providers are deactivated. Application services must filter soft-deleted records and enforce RBAC, consent, and tenant scope when those layers are introduced.

## Model inventory

| Domain | Tables |
| --- | --- |
| Identity and administration | users, roles, permissions, user_roles, role_permissions, departments, notifications, messages, audit_logs, ai_recommendations, system_settings |
| Central EMR | patients, doctors, specialties, appointments, medical_records, diagnoses, prescriptions, prescription_items, medications, vital_signs, nursing_notes, medical_attachments |
| Diagnostics and pharmacy | lab_orders, lab_results, radiology_orders, radiology_reports, pharmacy_inventory |
| Dentistry | dentists, dental_specialties, dental_records, dental_charts, dental_procedures, dental_images, orthodontic_cases |
| Rehabilitation | physical_therapists, therapy_assessments, therapy_sessions, therapy_plans, therapy_exercises, exercise_library, rehabilitation_progress, functional_outcomes, referrals, care_teams, care_team_members, multidisciplinary_cases |
| Women’s Health | womens_health_profiles, pregnancies, pregnancy_visits, antenatal_visits, obstetric_history, delivery_records, postpartum_visits, gynecology_journeys, gynecology_visits, infertility_journeys, infertility_cycles, partner_records, semen_analyses, folliculometry_records, follicle_measurements, ovulation_induction_cycles, iui_cycles, fertility_medication_protocols, womens_ultrasound_reports, fetal_biometry, fetal_doppler_records, gynecology_ultrasound_records, pregnancy_risk_flags, womens_health_calculations, womens_health_timeline_events |

## Core EMR relationship map

```text
User <-> Role <-> Permission
  |       Doctor -> Specialty
  |                    |
Patient -> Appointment <- Doctor
   |            |
   +------> MedicalRecord <------+
              |  |  |  |
        Diagnosis Rx Vitals NursingNote
              |
      Lab/Radiology Orders -> Results/Reports
```

The patient is the longitudinal identity. An appointment is scheduling context; a medical record is encounter context. Specialty records may link to both the patient and medical record, allowing specialty detail without fragmenting the central chart.

## Women’s Health relationship map

```text
Patient --1:1--> WomensHealthProfile
                    |-- Pregnancy --> Pregnancy/Antenatal Visits
                    |       |-------> Delivery, Postpartum, Risks
                    |       `-------> Ultrasound --> Biometry/Doppler
                    |-- GynecologyJourney --> GynecologyVisits
                    `-- InfertilityJourney --> InfertilityCycles
                              |                    |-- Folliculometry
                              |                    |-- Induction / IUI
                              `-- Partner --> SemenAnalyses
```

Women’s ultrasound reports can additionally reference the central medical record and radiology order. Timeline events provide a unified presentation index while source clinical records remain authoritative.

## Dentistry and rehabilitation

Dental records attach tooth charts, procedures, images, and orthodontic cases to a patient and optionally a central encounter. Rehabilitation assessments lead to plans, scheduled sessions, assigned exercises, progress observations, and functional outcomes. Referrals, care teams, and multidisciplinary cases are shared coordination primitives.

## Migration and seed commands

```powershell
flask --app app db upgrade
flask --app app seed-db
flask --app app db downgrade base
```

Set `SEED_ADMIN_PASSWORD` before seeding when possible. If omitted, the command prints a random password once. Seeding is idempotent and never resets an existing administrator’s password.

The initial revision is a frozen, explicit Phase 2 schema snapshot. Phase 3 and all later changes use separate forward revisions. Historical revisions are immutable. Subsequent changes should use `flask --app app db migrate -m "description"`, review the generated operations, and commit the revision.

## PostgreSQL and MySQL migration notes

- Run the full migration and test suite against the target engine before cutover.
- Use a supported UTF-8 encoding (`UTF8` on PostgreSQL or `utf8mb4` on MySQL).
- Verify index-length limits on MySQL and timezone behavior on both engines.
- Replace the database URL through environment configuration; do not alter model code or commit credentials.
- Export and validate data separately from schema migration, reconcile row counts, then switch traffic during a controlled maintenance window.
- UUID strings and generic JSON are intentionally portable. A later PostgreSQL-only optimization may convert them to native UUID/JSONB through explicit data migrations.

SQLite is suitable for local development and tests, not concurrent hospital production workloads. Production deployment also requires backup, recovery, encryption, retention, access-control, and compliance procedures outside the ORM layer.
