# iHIS User Management

## User workflow

Admin and Super Admin access `/users` to search, filter, create, inspect, and maintain accounts. Creation assigns one managed role and a temporary hashed password. Users are never deleted because their identities may be referenced by clinical records and audit events. Deactivation is the supported lifecycle control.

User department is the authoritative organizational assignment. Existing provider department fields remain for compatibility and are synchronized during management changes. Assigning Doctor or Women’s Health Doctor creates or reactivates a Doctor profile; specialty and license may remain incomplete until credentialing is finished. Removing the role deactivates that profile without deleting clinical history.

## Roles and permissions

The schema continues to support multiple roles, but Phase 4 forms intentionally manage one role per user. This keeps authorization and dashboard behavior predictable while preserving future extensibility.

- Super Admin can manage other users and operational role permissions and always bypasses permission checks.
- Admin can manage operational accounts but cannot manage Admin or Super Admin identities.
- Admin may view the role map but cannot change permission assignments.
- Super Admin role permissions cannot be restricted through the UI.
- No administrator can deactivate or administratively reset their own account.

Permission codes use `module.action`, including `users.view`, `users.manage`, `users.reset_password`, `roles.view`, and `roles.manage_permissions`.

## Password resets and activation

Administrative resets always hash the new temporary password, clear failed-login lockout state, and set `must_change_password`. Deactivated users are rejected by the existing authentication service and user loader. Personal password changes remain under `/auth/change-password` and require the current password.

## Audit logging

Creation, edits, role assignment, department changes, activation, deactivation, password resets, and role-permission changes write `audit_logs` entries. Before/after identifiers are recorded where useful; passwords and hashes are never included.

## Security notes

- All mutating browser actions use CSRF-protected POST forms.
- Server-side privilege checks remain authoritative even when controls are hidden.
- Search excludes soft-deleted records and is paginated.
- Unique usernames, emails, role names, and provider licenses remain database-enforced.
- Completing provider credentials before clinical signing is a later workflow requirement.

This phase does not implement HR records, employment contracts, payroll, scheduling, credential verification, or organizational hierarchy management.
