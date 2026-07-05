# Administration Module

## Administration workflow

The module provides operational oversight at `/administration`. Administrators use the dashboard to review daily, weekly, and monthly patient volumes, department performance, staff activity, resource utilization, operational KPIs, and a revenue placeholder. It intentionally excludes HR, payroll, accounting, and ERP workflows.

## Staff management

The staff view lists active and inactive users and supports filters for role, department, doctor specialty, and status. Staff assignments update the user's department. When the user has a doctor profile, its department is synchronized and an optional specialty can be assigned.

## Department management

Admin and Super Admin users can create, edit, activate, and deactivate departments. Supported types are Clinical, Laboratory, Radiology, Pharmacy, Reception, Nursing, Administration, Rehabilitation, Dentistry, and Women’s Health. Department codes and names must be unique.

## Resource allocation

The resource view assigns staff, doctors, and nurses through department membership. It shows active staffing and seven-day appointment workload. Room and clinic schedule allocation are labeled placeholders for a later phase.

## KPI logic

KPIs count appointments, completed visits, no-shows, laboratory orders, radiology orders, prescriptions, active patients, new patients, and department activity. Date, department, and doctor filters are applied where the underlying record carries those dimensions. Department completion rate is completed appointments divided by all appointments in the selected period.

## Permissions

- Super Admin has full access.
- Admin can view and manage the module.
- A user explicitly granted `administration.view` can view statistics and is restricted to their assigned department; this supports department-head access without introducing a new role.
- Management actions still require Admin or Super Admin.
- Clinical support roles and patients have no access unless the view permission is explicitly granted. Patients must never receive that permission.

## Audit logging

Audit events are written for department creation, update, activation/deactivation, staff assignment, KPI access, and report access. Events include the actor and relevant resource identifiers. Resource assignment changes are represented by staff-department assignment events; room and schedule audit events remain deferred with their placeholders.
