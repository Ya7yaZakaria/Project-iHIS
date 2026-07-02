# iHIS Architecture

## System vision

iHIS is a patient-centred, modular health information platform that connects clinical, diagnostic, operational, and administrative teams through one longitudinal record. Phase 1 provides extension boundaries only; it is not a deployable clinical system.

## Main portals

The dashboard shell reserves role-governed portals for patients, doctors, Women's Health clinicians, laboratories, radiology, pharmacy, dentistry, rehabilitation, nursing, reception, administration, and super administrators. Each portal will use the central identity, patient, EMR, notification, reporting, and audit capabilities rather than create isolated records.

## Module map

```text
Bootstrap UI / future REST clients
              |
       Flask blueprints
              |
         Domain services ---- Future AI adapters
              |
       SQLAlchemy models
              |
 SQLite -> PostgreSQL/MySQL
```

- `routes/` owns HTTP concerns and delegates future workflows to services.
- `services/` owns domain orchestration and integration boundaries.
- `models/` will own normalized persistence in Phase 2.
- Specialty records will reference the unified patient and EMR rather than duplicate demographics.
- Women's Health journeys will preserve pregnancy, gynecology, and infertility timelines within the longitudinal EMR.

## Database strategy

SQLite is the development default. SQLAlchemy and Alembic migrations through Flask-Migrate keep schema work portable to PostgreSQL or MySQL. Phase 2 will add foreign keys, indexes, timestamps, soft deletion, tenant-ready ownership keys, and explicit relationships. Database-specific SQL and SQLite-only types will be avoided. Migration files are generated only after models exist.

## Security strategy

- Flask-Login will manage authenticated sessions; CSRF protection is initialized globally.
- RBAC will be deny-by-default and enforced at routes and services, not merely hidden in menus.
- Passwords will use a modern adaptive hash; plaintext credentials will never be stored or logged.
- Security and clinical actions will produce append-oriented audit events with actor, action, target, time, request context, and outcome.
- Uploads will be private by default, size-limited, type-validated, renamed, malware-scan ready, and served only after authorization.
- Secrets come from environment or a future secret manager. Production deployments require HTTPS, secure cookies, encryption at rest, retention controls, backups, and jurisdiction-specific compliance review.
- Specialty access and patient consent rules will be designed before real clinical data is accepted.

## AI layer strategy

`services/ai/` defines inert interfaces so future providers do not leak into clinical modules. Implementations will receive only authorized, minimized context and return structured recommendations. AI output must be attributable, versioned, auditable, uncertainty-aware, and explicitly reviewed by a qualified human. AI services will not directly write diagnoses, prescriptions, or orders. Fallback behavior must leave normal clinical workflows available when AI is disabled or unavailable.

## Future upgrade strategy

- Move production persistence to managed PostgreSQL while retaining migration-tested dialect portability.
- Introduce hospital/tenant scope and isolation before multi-hospital deployment.
- Add versioned REST APIs and standards adapters for HL7/FHIR and DICOM/PACS.
- Isolate background work for reports, notifications, imaging, and AI behind queues when scale requires it.
- Support mobile and telemedicine clients through the same authorized service/API layer.
- Add centralized observability, immutable audit storage, disaster recovery, high availability, and staged deployment pipelines before production.
- Integrate wearables and national systems only through consent-aware, validated interoperability gateways.
