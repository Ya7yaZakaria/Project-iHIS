# Laboratory Module

## Workflow

Doctors create laboratory orders from an EMR visit. Orders retain patient, visit, ordering Doctor, optional catalog test, laboratory department, and assigned laboratory user links. The lifecycle is `requested` → `sample_collected` → `result_entered` → `verified` → `reviewed`; orders may be cancelled before verification.

## Test catalog

The catalog stores a unique code, name, category, default unit, reference range, sample type, turnaround time, and active status. Admin and Super Admin maintain catalog entries. Existing free-text EMR orders remain compatible.

## Samples and results

Check-in records the collector and collection timestamp. Laboratory users enter numeric, text, or qualitative results with units, reference ranges, comments, and Low/Normal/High/Critical flags. PDF or image attachments are stored privately under the configured upload directory.

Users with `laboratory.validate`, plus Admin and Super Admin, verify entered results. Critical verification creates an internal notification for the ordering Doctor. Only that Doctor can mark a verified result reviewed. Reviewed results are added to the EMR timeline.

## Access and auditing

- Laboratory users manage the worklist, samples, and result entry.
- Authorized validators and administrators verify results.
- Ordering Doctors view and review their own orders.
- Patients see only their own verified or reviewed results.
- Receptionists cannot enter or verify results.

Creation, updates, cancellation, collection, entry, verification, review, catalog changes, and attachments generate audit events without copying clinical values into audit details.

External analyzers, HL7/FHIR exchange, and AI interpretation are deferred. The normalized catalog and structured result fields provide the future integration boundary.
