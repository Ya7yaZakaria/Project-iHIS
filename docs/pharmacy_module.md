# Phase 9 — Pharmacy Module

## Medication catalog

Administrators manage generic and brand names, strength, dosage form, route, category, manufacturer, catalog code, barcode placeholder, and active status. Deactivation preserves prescriptions and inventory history while preventing new dispensing.

## Prescription workflow

Doctors create prescriptions from an EMR visit. New prescriptions remain `created` until the prescribing doctor explicitly sends them to pharmacy. The supported lifecycle is:

`created → sent_to_pharmacy → under_review → partially_dispensed | fully_dispensed`

A partially dispensed prescription remains actionable until a pharmacist closes it. `completed_at` identifies a closed partial outcome. Cancellation is permitted before dispensing begins and records the actor, time, and reason.

## Dispensing lifecycle

Only pharmacists or users with `pharmacy.dispense` may review and dispense. Each dispense validates the remaining prescribed quantity, medication status, batch ownership, expiry, and available balance in one database transaction. A selected substitute and explanation are stored as placeholders; no equivalence or clinical approval logic is included.

## Inventory and stock movements

Inventory is tracked by medication and unique batch number, with quantity, reorder level, expiry date, supplier placeholder, unit cost, and location. Automatic dispensing follows FEFO: non-expired batches with the earliest expiry are consumed first and a dispense can span batches. Pharmacists may override FEFO with one batch, but the requested quantity must be available in that batch.

Every addition and reduction creates an immutable stock movement containing a signed quantity and post-movement balance. Stock cannot become negative. Expired means an expiry date earlier than today; stock expiring today remains usable. Low stock compares total usable stock with the highest configured reorder level among the medication's batches.

## EMR integration

Visit details show prescription status, quantities, pharmacy notes, and the send action. Successful dispensing upserts a patient medication-history entry for the prescription item. `/patients/<id>/medication-history` presents the longitudinal dispensing record.

## Permissions

- Doctor: create and send own prescriptions; view dispensing progress.
- Pharmacist: review and dispense; manage inventory only with `pharmacy.manage_inventory`.
- Admin/Super Admin: manage the medication catalog and view pharmacy operations.
- Patient: view only medication history linked to their own patient profile.
- Receptionist: no dispensing or inventory access.

## Audit logging

Audit events cover medication creation/update/deactivation, sending, review, cancellation, dispensing, completion, stock additions/reductions, and medication-history updates. Events include the actor and affected resource identifiers.

## Deferred work

Insurance billing, external pharmacy integration, barcode scanning, purchasing, pricing workflows, and substitution approval are intentionally excluded.
