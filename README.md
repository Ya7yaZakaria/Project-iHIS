# Intelligent Health Information System (iHIS)

Phase 3 adds secure Flask-Login authentication, temporary lockout, RBAC route protection, audit events, and admin-controlled registration. Full user management, clinical CRUD workflows, and AI inference remain out of scope.

## Quick start

1. Create and activate a Python 3.11+ virtual environment.
2. Run `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and replace `SECRET_KEY`.
4. Run `flask --app app run` or `python app.py`.
5. Run `flask --app app db upgrade`.
6. Set `SEED_ADMIN_PASSWORD`, then run `flask --app app seed-db`.
7. Open `http://127.0.0.1:5000`.

Run scaffold checks with `pytest`.

After pulling any change that includes models or migration files, stop the development server and run `python -m flask db upgrade` before restarting it. Use `python -m flask db current` to confirm the live database revision.

## Architecture

- `app.py` owns the application factory, extension initialization, blueprints, logging, and errors.
- `models/` contains normalized core and specialty SQLAlchemy models.
- `routes/` defines stable modular blueprint boundaries.
- `services/` separates clinical/domain operations from transport and persistence.
- `services/ai/` exposes inert future AI interfaces; all methods currently use `pass`.
- `templates/` and `static/` provide the responsive Bootstrap dashboard shell.

Detailed design decisions are in [docs/architecture.md](docs/architecture.md).
The schema inventory and relationship maps are in [docs/database_models.md](docs/database_models.md).
Authentication flows and the role access map are in [docs/authentication.md](docs/authentication.md).
Administrative user workflows are in [docs/user_management.md](docs/user_management.md).
The central clinical-record workflow is in [docs/emr_module.md](docs/emr_module.md).

## Phase boundary

The next phase implements authentication around the existing Flask-Login-compatible user and RBAC models. CRUD/API behavior, role enforcement, clinical workflows, and AI implementations remain later roadmap phases.

> This foundation is not ready for clinical use. It stores no patient data and makes no clinical decisions.
