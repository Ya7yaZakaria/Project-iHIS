# Dashboard UI

## Dashboard structure

All portal dashboards use the global `base.html` shell and the shared dashboard layout. The shell provides the responsive sidebar, top navigation, profile menu, breadcrumbs, flash messages, dark-mode preference, RTL hooks, and confirmation modal. Dashboard pages add metric cards, worklists, alerts, quick actions, empty/loading states, filters, and chart placeholders.

## Role dashboard map

`/dashboard` redirects authenticated users according to their primary role. Dedicated routes exist for Super Admin, Admin, Doctor, Women’s Health Doctor, Receptionist, Nurse, Laboratory, Radiology, Pharmacist, Dentist, Rehabilitation Specialist, and Patient.

Super Admin may open every dashboard. Every other user may open only their exact role dashboard; Admin is limited to the Admin dashboard. A role mismatch returns HTTP 403.

## Widget map

- Doctor: appointments, pending reports, follow-ups, critical-patient and AI placeholders.
- Women’s Health: pregnancy, risk, ANC, infertility, IUI, folliculometry, and postpartum indicators.
- Reception: appointments, queue, check-ins, walk-ins, no-shows, and follow-ups.
- Nursing: assigned patients, vitals, medication tasks, alerts, and recent notes.
- Laboratory, Radiology, and Pharmacy: operational work queues, verification, exceptions, and inventory indicators.
- Admin: patient volume, department performance, staffing, operational KPIs, and revenue placeholder.
- Super Admin: users, system/security summaries, audit activity, logs, and backup placeholders.
- Patient: appointments, laboratory activity, medications, alerts, documents, and AI-insight placeholder.
- Dentistry and Rehabilitation: active records, recent activity, follow-ups, and alerts.

## UI component rules

Use Bootstrap responsive grid classes, semantic headings, accessible labels, table wrappers, standard status badges, and visible empty states. Quick actions must link only to existing authorized workflows. Filters are client-side for rendered tables or ordinary query-string submissions. Destructive actions use the shared confirmation modal.

## Navigation and permissions

Sidebar links are rendered from authenticated role membership. Hiding a link is not authorization: dashboard routes independently enforce role access. Domain routes such as `/laboratory` and `/reception` remain separate from their dashboard entrypoints.

## Future upgrades

Chart surfaces, real-time refresh, critical notifications, system monitoring, AI insights, revenue analytics, and backup/restore are placeholders. Later phases may replace them with audited APIs and live visualization without changing the dashboard data contract.
