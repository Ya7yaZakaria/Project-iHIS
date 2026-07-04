# Phase 8 — Radiology Module

## Overview

The Radiology Module manages imaging orders, workflow, reporting, verification, review, and EMR integration.

---

# Features

## Imaging Catalog

- Imaging study catalog
- Modality management
- Body region
- Preparation instructions
- Active / inactive studies

Supported modalities:

- X-ray
- Ultrasound
- CT
- MRI
- Mammography
- Doppler
- Other

---

## Radiology Orders

Doctors can create imaging orders linked to:

- Patient
- Medical Record
- Ordering Doctor
- Imaging Study

Each order stores:

- Clinical indication
- Priority
- Modality
- Body part

---

## Workflow

Status lifecycle:

Requested

↓

Scheduled

↓

Patient Arrived

↓

Imaging Performed

↓

Report Drafted

↓

Report Verified

↓

Reviewed by Doctor

↓

Completed

Cancelled orders terminate the workflow.

---

## Radiology Report

Each report contains:

- Clinical indication
- Technique
- Findings
- Impression
- Recommendations
- Radiologist
- Report timestamp

Flags:

- Abnormal
- Critical

---

## Attachments

Supported:

- Images
- PDF reports
- Future DICOM files

Stored separately from report text.

---

## Patient Portal

Patients can view:

- Verified reports
- Reviewed reports

Patients cannot access:

- Draft reports
- Unverified reports

---

## Doctor Review

Ordering doctor reviews verified reports.

Review timestamp is stored.

---

## Dashboard

Widgets:

- Pending orders
- Scheduled today
- Performed today
- Awaiting verification
- Urgent findings
- Completed today

---

## EMR Integration

Radiology orders are linked to:

- Patient
- Medical Record
- Timeline

Reports become visible after verification.

---

## Permissions

Doctor

- Create orders
- Review reports

Radiology

- Schedule
- Perform imaging
- Draft reports

Radiologist

- Verify reports

Patient

- View verified reports only

Admin

- Full access
- Manage imaging catalog

---

## Audit Logging

The following actions are audited:

- Order creation
- Order update
- Scheduling
- Patient arrival
- Imaging performed
- Report creation
- Report verification
- Doctor review
- File attachment
- Cancellation

---

## Future AI Hooks

Reserved integration points:

- AI image interpretation
- AI report drafting
- AI triage
- AI quality assurance

Not implemented:

- PACS
- DICOM viewer
- AI diagnosis

These features are intentionally deferred.