from datetime import timedelta

from extensions import db
from models import AuditLog, Permission, Role, User
from models.base import utcnow


def make_user(session, role_name="Doctor", username="doctor1", active=True, permission=None):
    role = session.execute(db.select(Role).filter_by(name=role_name)).scalar_one_or_none()
    if role is None:
        role = Role(name=role_name)
        session.add(role)
    if permission:
        assigned = next((item for item in role.permissions if item.code == permission), None)
        if assigned is None:
            assigned = session.execute(db.select(Permission).filter_by(code=permission)).scalar_one_or_none()
        if assigned is None:
            assigned = Permission(code=permission, module=permission.split(".")[0], action=permission.split(".")[1])
            role.permissions.append(assigned)
    user = User(username=username, email=f"{username}@example.test", first_name="Ada", last_name="Care", roles=[role], is_active=active)
    user.set_password("safe-test-password")
    session.add(user)
    session.commit()
    return user


def login(client, identifier="doctor1", password="safe-test-password", follow=False, **extra):
    return client.post("/auth/login", data={"identifier": identifier, "password": password, **extra}, follow_redirects=follow)


def test_password_hash_and_compatibility_properties(session):
    user = make_user(session)
    assert user.password_hash != "safe-test-password"
    assert user.check_password("safe-test-password")
    assert user.full_name == "Ada Care"
    assert user.role_id == user.roles[0].id


def test_successful_login_by_username_and_role_redirect(client, session):
    user = make_user(session)
    response = login(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard/doctor")
    session.refresh(user)
    assert user.last_login_at is not None
    assert session.query(AuditLog).filter_by(action="auth.login_succeeded").count() == 1


def test_login_by_email_and_remember_cookie(client, session):
    make_user(session)
    response = login(client, identifier="doctor1@example.test", remember="y")
    assert "remember_token=" in " ".join(response.headers.getlist("Set-Cookie"))


def test_failed_login_and_lockout(client, session):
    user = make_user(session)
    for _ in range(5):
        response = login(client, password="incorrect", follow=True)
    session.refresh(user)
    assert b"invalid username/email or password" in response.data.lower()
    assert user.failed_login_attempts == 5
    assert user.is_locked
    assert session.query(AuditLog).filter_by(action="auth.login_failed").count() == 5


def test_inactive_and_existing_lockout_block_login(client, session):
    make_user(session, username="inactive", active=False)
    locked = make_user(session, username="locked")
    locked.locked_until = utcnow() + timedelta(minutes=10)
    session.commit()
    assert login(client, identifier="inactive").status_code == 200
    assert login(client, identifier="locked").status_code == 200


def test_logout_and_protected_route(client, session):
    make_user(session)
    assert client.get("/dashboard/doctor").status_code == 302
    login(client)
    response = client.get("/auth/logout")
    assert response.status_code == 302
    assert client.get("/dashboard/doctor").status_code == 302
    assert session.query(AuditLog).filter_by(action="auth.logout").count() == 1


def test_wrong_role_is_forbidden(client, session):
    make_user(session, role_name="Patient")
    login(client)
    assert client.get("/dashboard/doctor").status_code == 403
    assert client.get("/dashboard/patient").status_code == 200


def test_external_next_redirect_is_rejected(client, session):
    make_user(session)
    response = client.post("/auth/login?next=https://evil.example", data={"identifier": "doctor1", "password": "safe-test-password"})
    assert response.headers["Location"].endswith("/dashboard/doctor")


def test_admin_can_register_operational_user(client, session):
    admin = make_user(session, role_name="Admin", username="admin")
    patient_role = Role(name="Patient")
    session.add(patient_role)
    session.commit()
    login(client, identifier=admin.username)
    response = client.post("/auth/register", data={
        "username": "newpatient", "email": "new@example.test", "first_name": "New",
        "last_name": "Patient", "role_id": patient_role.id,
        "password": "temporary-password", "confirm_password": "temporary-password",
    })
    assert response.status_code == 302
    assert session.execute(db.select(User).filter_by(username="newpatient")).scalar_one().has_role("Patient")


def test_non_admin_cannot_register(client, session):
    make_user(session, role_name="Doctor")
    login(client)
    assert client.get("/auth/register").status_code == 403


def test_change_password(client, session):
    user = make_user(session)
    login(client)
    response = client.post("/auth/change-password", data={"current_password": "safe-test-password", "new_password": "new-safe-password", "confirm_password": "new-safe-password"})
    assert response.status_code == 302
    session.refresh(user)
    assert user.check_password("new-safe-password")
    assert session.query(AuditLog).filter_by(action="auth.password_changed").count() == 1
