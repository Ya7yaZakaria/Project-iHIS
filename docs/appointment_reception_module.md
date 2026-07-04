# Appointment and Reception Module

## Appointment workflow

Receptionists and administrators book appointments against an existing patient, with an optional Doctor and department. The Doctor's specialty is displayed through the linked Doctor profile. Appointment updates, cancellation, and rescheduling retain the original appointment identifier and audit history.

The supported lifecycle is `booked` or `confirmed`, then `arrived`, `waiting`, `in_consultation`, and `completed`. Cancellation and no-show are terminal outcomes. A completed appointment can produce a separately linked follow-up appointment.

## Reception workflow

Reception can search or register patients, with duplicate checking based on normalized name plus phone and date of birth. Check-in records arrival time, reception notes, and the next queue number for the appointment day. The reception dashboard summarizes today's volume, waiting patients, completed visits, no-shows, the next appointment, and Doctor workload.

The live queue contains arrived, waiting, and in-consultation appointments. It is ordered by queue number and arrival time. Starting a consultation creates or reuses a draft medical record linked to the appointment.

## Permissions

| Role | Access |
|---|---|
| Super Admin / Admin | View and manage all appointments and reception workflows |
| Receptionist | Register demographics, book/manage appointments, check in, and manage the queue |
| Doctor | View assigned appointments and start/complete assigned consultations |
| Patient | Read only their own appointment list and details |

Patients cannot see internal or reception notes. Reception staff cannot edit clinical notes. All state-changing endpoints use CSRF-protected POST requests.

## Audit logging

The service records appointment creation, update, cancellation, rescheduling, arrival, waiting, no-show, consultation start, completion, and follow-up scheduling. Audit records contain identifiers and workflow context, not clinical note content.

## Migration and deferred work

The Phase 6 migration adds arrival, consultation, cancellation, queue, reception-note, and follow-up fields with indexes and foreign keys. Run `python -m flask db upgrade` before starting the application. Billing, advanced calendar interfaces, notification delivery, national-ID matching, and a full patient portal remain future work.
