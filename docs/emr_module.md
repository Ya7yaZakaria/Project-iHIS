# iHIS Central EMR

## Workflow and record structure

The Patient record is the longitudinal identity. Authorized demographic staff register demographics, histories, allergies, chronic conditions, vaccinations, and an MRN. MRNs are generated when omitted and authorized overrides are unique and audited.

A `MedicalRecord` represents one clinical visit and links the patient, authoring Doctor, optional appointment, diagnoses, prescriptions, orders, vitals, nursing notes, attachments, and follow-up. Standard notes and SOAP fields coexist so specialty modules can extend the encounter without fragmenting the central chart.

## Timeline

`build_patient_timeline()` returns reverse-chronological events for visits, diagnoses, prescriptions, Lab orders, Radiology orders, documents, and scheduled follow-ups. Timeline entries contain only presentation metadata and retain links to their authoritative records.

## Prescriptions

`Prescription` is the visit-level header. Each `PrescriptionItem` references a normalized Medication and stores dose, route, frequency, duration, quantity, and instructions. Migration `0004` preserves every legacy prescription by creating one item before removing medication fields from the header. PDF printing remains a placeholder.

## Investigation orders

Doctors create Lab and Radiology requests from a visit. Supported workflow states are `requested`, `pending`, `completed`, and `reviewed`. Result entry, validation, DICOM, and report workflows remain in their dedicated phases.

## Attachments

Documents are stored outside `static` under `uploads/emr/<patient-id>/` with UUID filenames. The system validates allowed extensions, size, basic file signatures, non-empty content, path containment, and SHA-256 checksum. Original names are metadata only. Downloads pass through an authorized route and never expose raw storage paths.

## Access control

- Super Admin may inspect every EMR but cannot author clinical records without an active Doctor profile.
- Doctors require an appointment, an authored visit, or care-team membership.
- Nurses require care-team membership and may add vitals and nursing notes only.
- Reception/Admin maintain demographics but cannot edit clinical notes.
- Patient accounts receive read-only access only to their linked Patient record.
- Laboratory and Radiology staff use their order modules and cannot edit clinical notes.

Every EMR view and clinical modification is audited using identifiers and outcomes rather than clinical narrative content. Denied EMR access is also recorded.

## Extension boundaries

Women’s Health, Dentistry, Rehabilitation, Laboratory results, Radiology reports, clinical signing, coding lookup, billing, interoperability, and AI support extend this central record in later phases. Phase 5 does not duplicate their specialty workflows.
