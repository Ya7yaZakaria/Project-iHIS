# iHIS Authentication and RBAC

## Authentication flow

Users sign in at `/auth/login` with either username or email. The service normalizes the identifier, verifies account state and temporary lockout, checks the Werkzeug password hash, resets failed attempts, updates the last-login time, writes an audit event, and starts a Flask-Login session. Only local `next` paths are accepted. Logout records an audit event before clearing the session.

Registration is restricted to Admin and Super Admin. Admins may assign operational roles; only Super Admin may assign Admin or Super Admin. Newly registered users receive one initial role through the normalized `user_roles` association and must change their temporary password.

The forgot-password page is informational. No reset token or email workflow exists in this phase.

## RBAC design

Users may hold multiple roles. `primary_role` follows deterministic priority and controls the default dashboard; `role_id` is a read-only compatibility property. Authorization checks all assigned roles and permissions. Super Admin bypasses role and permission checks.

| Role | Primary access |
| --- | --- |
| Super Admin | All routes and dashboards |
| Admin | Administration, reports, operational registration |
| Doctor | Doctor workspace and EMR |
| Women’s Health Doctor | Doctor, EMR, and Women’s Health |
| Receptionist | Patient registration and appointments |
| Nurse | Nursing notes and vital signs permissions |
| Laboratory | Laboratory orders and results |
| Radiology | Imaging orders and reports |
| Pharmacist | Prescriptions and inventory |
| Dentist | Dentistry |
| Rehabilitation Specialist | Rehabilitation |
| Patient | Patient portal |

Use `login_required` for authentication, `role_required(...)` for portal boundaries, and `permission_required("module.action")` for granular operations. Hiding navigation is not authorization; server-side decorators remain authoritative.

## Password and lockout security

Passwords are never stored or logged in plaintext. Werkzeug adaptive hashing is used. Registration and password changes require at least eight characters. Five consecutive failures lock an account for fifteen minutes by default; successful login resets the counter. Configure these values through environment variables.

Inactive and soft-deleted accounts cannot sign in. Error messages avoid revealing whether an unknown identifier exists, except that administratively disabled accounts receive an explicit support message after matching a known account.

## Session management

Session and remember cookies are HTTP-only and SameSite=Lax. Production configuration forces Secure cookies. Normal sessions last eight hours and remember-me cookies fourteen days by default. Login clears previous session state, and logout clears the authenticated session.

## Audit logging

Successful login, failed login, lockout, logout, registration, and password changes write append-oriented `audit_logs` entries. Events include action, outcome, actor/target IDs when available, IP address, user agent, and limited context. Unknown identifiers are represented by a short one-way fingerprint. Passwords and hashes are never included.

## Future upgrades

Future security phases may add TOTP/WebAuthn 2FA, signed email-reset tokens, OAuth/OIDC, enterprise SSO, session/device inventory, remote revocation, breached-password screening, risk-based authentication, and centralized security monitoring. These should extend the current service and audit boundaries rather than bypass them.
