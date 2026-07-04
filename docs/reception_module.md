# Phase 14 — Reception Module

## Goal

The Reception module expands front-desk operations beyond basic appointments.

It supports:

- Daily reception dashboard
- Patient registration
- Patient search
- Duplicate prevention
- Appointment check-in
- Queue management
- Walk-in creation
- Follow-up booking
- Billing initiation placeholder

This phase does not implement full accounting or clinical editing.

---

## Reception Workflow

1. Receptionist opens `/reception`.
2. Receptionist searches for the patient before creating a new record.
3. If no duplicate is found, receptionist registers the patient.
4. Receptionist checks in booked patients.
5. Patient is added to the clinic queue.
6. Receptionist updates queue status.
7. Doctor can view the queue.
8. Receptionist can create walk-ins and follow-up bookings.
9. Receptionist can start a billing placeholder.

---

## Patient Registration Workflow

Route:

- `/reception/register-patient`

Receptionist can create a quick patient profile with:

- Medical record number
- First name
- Last name
- Date of birth
- Sex at birth
- Phone
- Email
- Address

National ID is currently a placeholder only and is not stored because the Patient model does not yet include a national ID field.

---

## Duplicate Prevention Logic

Duplicate prevention checks:

- Phone if provided
- Email if provided
- First name + last name + date of birth

If a possible duplicate is found, registration is blocked and the receptionist should review the existing patient.

---

## Patient Search Workflow

Route:

- `/reception/search-patient`

Search supports:

- Name
- Phone
- Medical record number
- Email
- Date of birth

Search is intended to reduce duplicate patient records.

---

## Check-in Workflow

Route:

- `/reception/check-in`

Check-in:

- Confirms arrival
- Sets arrival time
- Assigns queue number
- Stores reception notes
- Adds patient to queue

Appointment data is reused instead of creating a separate queue model.

---

## Queue Lifecycle

Route:

- `/reception/queue`

Supported queue statuses:

- Waiting
- Called placeholder
- In consultation
- Completed
- Cancelled
- No-show

Manual queue reorder is supported by changing `queue_number`.

---

## Walk-in Workflow

Route:

- `/reception/walk-in`

Receptionist can:

- Select existing patient
- Or create a new minimal patient profile
- Create walk-in appointment
- Mark patient arrived
- Assign queue number

---

## Follow-up Booking

Route:

- `/reception/follow-up`

Receptionist can book a follow-up appointment linked to:

- Patient
- Optional previous appointment
- Optional doctor placeholder
- Reason
- Notes

---

## Billing Initiation Placeholder

Route:

- `/reception/billing-initiation`

The billing placeholder stores:

- Patient
- Optional appointment
- Status
- Notes
- Started by user

Statuses:

- Not started
- Pending
- Paid
- Cancelled

This does not implement invoices, payments, accounting, insurance, or financial reporting.

---

## Permissions

Receptionist can:

- Register patients
- Search patients
- Update demographics through reception service
- Check in patients
- Manage queue
- Create walk-ins
- Book follow-ups
- Initiate billing placeholder

Doctor can:

- View queue

Admin and Super Admin can:

- Access all reception workflows

Receptionist cannot:

- Edit clinical notes
- Edit doctor diagnosis
- Edit prescriptions
- Access sensitive EMR details through this module

---

## Audit Logging

The module logs:

- Patient registration
- Demographic update
- Check-in
- Queue add
- Queue status update
- Queue reorder
- Walk-in creation
- Follow-up booking
- Billing initiation

Audit rows are stored in `audit_logs`.

---

## Database

New table:

- `billing_initiations`

Fields:

- patient_id
- appointment_id
- status
- started_by_id
- notes

Queue and check-in reuse existing `appointments` fields:

- status
- arrival_time
- queue_number
- reception_notes
- follow_up_of_id

---

## Tests

Covered by:

- `tests/test_reception_module.py`

Test coverage includes:

- Receptionist can register patient
- Duplicate prevention works
- Patient search works
- Check-in works
- Queue status update works
- Queue reorder works
- Walk-in creation works
- Follow-up booking works
- Billing initiation works
- Unauthorized user cannot access reception services