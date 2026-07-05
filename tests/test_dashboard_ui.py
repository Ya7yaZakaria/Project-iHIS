"""Phase 16 unified dashboard UI tests."""

import pytest

from extensions import db
from models import Role, User
from services.dashboard_service import get_dashboard_for_role


ROLE_PATHS = {
    "Super Admin": "/dashboard/super-admin", "Admin": "/dashboard/admin",
    "Doctor": "/dashboard/doctor", "Women’s Health Doctor": "/dashboard/womens-health",
    "Receptionist": "/dashboard/reception", "Nurse": "/dashboard/nursing",
    "Laboratory": "/dashboard/laboratory", "Radiology": "/dashboard/radiology",
    "Pharmacist": "/dashboard/pharmacy", "Dentist": "/dashboard/dentistry",
    "Rehabilitation Specialist": "/dashboard/rehabilitation", "Patient": "/dashboard/patient",
}


def _user(session, role_name, suffix):
    role = session.scalar(db.select(Role).where(Role.name == role_name))
    if role is None:
        role = Role(name=role_name); session.add(role)
    user = User(username=f"dash-{suffix}", email=f"dash-{suffix}@test.local",
                first_name="Dashboard", last_name=suffix, roles=[role])
    user.set_password("test-password"); session.add(user); session.commit()
    return user


def _login(client, user):
    with client.session_transaction() as state:
        state["_user_id"] = user.id; state["_fresh"] = True


@pytest.mark.parametrize("role_name,path", ROLE_PATHS.items())
def test_each_role_redirects_to_correct_dashboard(client, session, role_name, path):
    user = _user(session, role_name, role_name.lower().replace(" ", "-").replace("’", ""))
    _login(client, user)
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert response.headers["Location"].endswith(path)


def test_role_mismatch_is_forbidden(client, session):
    patient = _user(session, "Patient", "mismatch")
    _login(client, patient)
    assert client.get("/dashboard/doctor").status_code == 403
    assert client.get("/dashboard/patient").status_code == 200


def test_super_admin_can_render_all_dashboards(client, session):
    admin = _user(session, "Super Admin", "super")
    _login(client, admin)
    for path in ROLE_PATHS.values():
        assert client.get(path).status_code == 200


def test_admin_access_boundary(client, session):
    admin = _user(session, "Admin", "admin")
    _login(client, admin)
    assert client.get("/dashboard/admin").status_code == 200
    assert client.get("/dashboard/doctor").status_code == 403
    assert client.get("/dashboard/super-admin").status_code == 403


@pytest.mark.parametrize("role_name", ROLE_PATHS)
def test_dashboard_service_has_stable_structure(session, role_name):
    user = _user(session, role_name, f"service-{len(session.new)}-{role_name.lower().replace(' ', '-')}")
    data = get_dashboard_for_role(user)
    assert {"metrics", "worklists", "alerts", "recent_activity", "quick_actions", "placeholders"} <= data.keys()


def test_mobile_shell_and_widgets_render(client, session):
    patient = _user(session, "Patient", "mobile")
    _login(client, patient)
    response = client.get("/dashboard/patient")
    assert response.status_code == 200
    assert b'data-bs-target="#sidebar"' in response.data
    assert b"col-6 col-xl-3" in response.data
    assert b"confirmationModal" in response.data
    assert b"Nothing needs attention" in response.data
