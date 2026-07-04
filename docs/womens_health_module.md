# Phase 10 — Women's Health Module

## Women's Health workflow

Each patient may have one longitudinal Women's Health profile containing menstrual, contraception, gynecology, infertility, surgical, and risk summaries. Pregnancy, gynecology, and infertility journeys remain independent; creating a journey marks it as the current journey without closing other active journeys.

Clinical records start as drafts. A Women's Health Doctor signs a complete record before it becomes visible in the patient portal. Signing is an approval/release action, not an AI decision.

## Pregnancy and ANC

A pregnancy requires an LMP or EDD. EDD defaults to LMP plus 280 days. Gravidity, parity, abortions, living children, previous caesarean/vaginal births, maternal/fetal conditions, and risk flags are retained.

An ANC entry atomically creates a clinical pregnancy visit and its measurement record. GA is calculated at the visit date. Nurses with `womens_health.record_anc_basic` may enter weight, BP, urine, fetal heart rate, fundal height, movement, and presentation. Complaint, assessment, plan, signing, delivery, and postpartum documentation remain physician responsibilities.

## Ultrasound

Women's ultrasound supports obstetric, gynecology, folliculometry, fetal biometry, and Doppler scans. Reports may link to pregnancy, ANC/pregnancy visits, gynecology or infertility journeys, EMR visits, and optional Radiology orders. Placenta, liquor, cervical length, findings, impression, measurements, fetal biometry, and Doppler structures are available.

Attachments are stored beneath the configured upload root with generated names, checksums, metadata, path-containment checks, and authenticated downloads. Patients may download only attachments belonging to signed reports.

## Gynecology

Gynecology journeys group longitudinal visits around a primary condition. Visits capture symptoms, examination, diagnosis, assessment, procedures, treatment plan, and follow-up.

## Infertility, OITI, and IUI

Infertility journeys support primary/secondary infertility, duration, female/male factors, investigations, treatment plans, partner records, and semen analyses. Treatment cycles hold cycle LMP, protocol, medication summary, trigger information, timed-intercourse advice, status, and outcome.

Folliculometry records calculate cycle day from LMP and store endometrial findings plus individual left/right follicle measurements. IUI records support stimulation, trigger, linked partner/semen analysis, semen preparation, post-wash count, procedure date, luteal support, pregnancy-test date, and outcome. IVF laboratory and embryology are intentionally excluded.

## Calculations

- EDD: LMP + 280 days.
- GA: elapsed days from LMP, or an LMP inferred as EDD − 280 days, returned as weeks and days.
- Cycle day: inclusive day count beginning at 1.
- BMI: weight in kilograms divided by height in metres squared.
- Pregnancy risk summary: descriptive placeholder only; physician assessment is mandatory.

## EMR integration

Profile, pregnancy, ANC, ultrasound, gynecology, infertility cycle, folliculometry, IUI, delivery, and postpartum operations create timeline events. The central EMR timeline includes these events. Patient timelines filter out unsigned Women's Health sources.

## Permissions and audit

- Women's Health Doctor: full create/update/sign access.
- Admin/Super Admin: full operational access.
- Doctor: view only when granted `womens_health.view`.
- Nurse: basic ANC measurements only with `womens_health.record_anc_basic`.
- Patient: own signed records only.
- Reception, Laboratory, and Radiology receive no general Women's Health access.

Profile, pregnancy, ANC, ultrasound/attachments, gynecology, infertility, partner, semen analysis, folliculometry, IUI, delivery, postpartum, and signing actions emit audit events with actor and resource identifiers.

## Future AI hooks

The obstetric, gynecology, infertility, ultrasound, pregnancy-risk, and folliculometry assistant classes are non-operational extension points. Phase 10 performs no model calls, automated diagnosis, treatment recommendation, or replacement of physician judgment.
