"""Phase 15 administration module tests."""

from extensions import db
from models import Appointment, Department, Role, User
from services.administration_service import assign_staff_to_department, get_operational_kpis


def _user(session, suffix, role_name):
    role = session.scalar(db.select(Role).where(Role.name == role_name))
    if role is None:
        role = Role(name=role_name)
        session.add(role)
    user = User(username=f"admin-{suffix}", email=f"admin-{suffix}@test.local",
                first_name="Test", last_name=suffix, roles=[role])
    user.set_password("test-password")
    session.add(user)
    session.commit()
    return user


def _login(client, user):
    with client.session_transaction() as state:
        state["_user_id"] = user.id
        state["_fresh"] = True


def test_admin_can_access_administration_dashboard(client, session):
    admin = _user(session, "dashboard", "Admin")
    _login(client, admin)
    response = client.get("/administration/")
    assert response.status_code == 200
    assert b"Administration dashboard" in response.data


def test_non_admin_cannot_access_administration_dashboard(client, session):
    user = _user(session, "patient", "Patient")
    _login(client, user)
    assert client.get("/administration/").status_code == 403


def test_department_creation_works(client, session):
    admin = _user(session, "create", "Admin")
    _login(client, admin)
    response = client.post("/administration/departments/create", data={
        "code": "CARD", "name": "Cardiology", "department_type": "Clinical",
        "location": "First floor", "description": "Heart clinic",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert session.scalar(db.select(Department).where(Department.code == "CARD")) is not None


def test_staff_assignment_works(session):
    admin = _user(session, "assigner", "Admin")
    staff = _user(session, "staff", "Nurse")
    department = Department(code="NURS", name="Nursing", department_type="Nursing")
    session.add(department)
    session.commit()
    assign_staff_to_department(staff, department, admin)
    assert staff.department_id == department.id


def test_kpi_service_returns_data(session):
    data = get_operational_kpis()
    assert {"appointments", "completed_visits", "no_shows", "lab_orders",
            "radiology_orders", "prescriptions", "active_patients", "new_patients"} <= data.keys()


def test_unauthorized_user_cannot_manage_departments(client, session):
    user = _user(session, "nurse", "Nurse")
    _login(client, user)
    assert client.post("/administration/departments/create", data={
        "code": "NO", "name": "Not Allowed", "department_type": "Clinical",
    }).status_code == 403
