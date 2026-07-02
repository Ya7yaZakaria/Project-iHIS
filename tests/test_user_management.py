from models import AuditLog, Department, Doctor, Permission, Role, Specialty, User
from services.user_management_service import (activate_user, assign_permissions,
                                               create_user, deactivate_user,
                                               reset_user_password, search_users,
                                               update_user)


def make_actor(session, role_name="Admin", username="manager"):
    role = Role(name=role_name)
    actor = User(username=username, email=f"{username}@example.test", first_name="User", last_name="Manager", roles=[role])
    actor.set_password("manager-password")
    session.add(actor)
    session.commit()
    return actor


def login(client, username="manager", password="manager-password"):
    return client.post("/auth/login", data={"identifier": username, "password": password})


def test_admin_creates_operational_user_with_hashed_password(session):
    actor = make_actor(session)
    role = Role(name="Patient")
    department = Department(code="OPD-T", name="Outpatient Test")
    session.add_all([role, department])
    session.commit()
    user = create_user(username="New.User", email="NEW@EXAMPLE.TEST", first_name="New", last_name="User", password="temporary-password", role=role, department_id=department.id, actor=actor)
    assert user.username == "new.user"
    assert user.department is department
    assert user.check_password("temporary-password")
    assert user.password_hash != "temporary-password"
    assert session.query(AuditLog).filter_by(action="users.created").count() == 1


def test_non_admin_cannot_create_user(session):
    actor = make_actor(session, role_name="Doctor")
    role = Role(name="Patient")
    session.add(role)
    session.commit()
    try:
        create_user(username="blocked", email="blocked@example.test", first_name="No", last_name="Access", password="temporary-password", role=role, actor=actor)
        assert False, "Expected PermissionError"
    except PermissionError:
        pass


def test_admin_cannot_assign_administrative_role(session):
    actor = make_actor(session)
    protected_role = Role(name="Super Admin")
    session.add(protected_role)
    session.commit()
    try:
        create_user(username="escalated", email="escalated@example.test", first_name="No", last_name="Escalation", password="temporary-password", role=protected_role, actor=actor)
        assert False, "Expected PermissionError"
    except PermissionError:
        pass


def test_doctor_profile_can_be_incomplete_and_department_is_synchronized(session):
    actor = make_actor(session, role_name="Super Admin")
    doctor_role = Role(name="Doctor")
    patient_role = Role(name="Patient")
    department = Department(code="CARD-T", name="Cardiology Test")
    specialty = Specialty(code="CARD-T", name="Test Cardiology")
    session.add_all([doctor_role, patient_role, department, specialty])
    session.commit()
    user = create_user(username="newdoctor", email="newdoctor@example.test", first_name="New", last_name="Doctor", password="temporary-password", role=doctor_role, department_id=department.id, actor=actor)
    assert user.doctor_profile is not None
    assert user.doctor_profile.specialty_id is None
    assert user.doctor_profile.license_number is None
    assert user.doctor_profile.department_id == department.id
    update_user(user, username=user.username, email=user.email, first_name=user.first_name, last_name=user.last_name, phone=None, role=doctor_role, department_id=department.id, specialty_id=specialty.id, license_number="LIC-P4", actor=actor)
    assert user.doctor_profile.specialty is specialty
    update_user(user, username=user.username, email=user.email, first_name=user.first_name, last_name=user.last_name, phone=None, role=patient_role, actor=actor)
    assert not user.doctor_profile.is_active


def test_activation_deactivation_and_password_reset(session):
    actor = make_actor(session)
    role = Role(name="Patient")
    session.add(role)
    session.commit()
    user = create_user(username="lifecycle", email="lifecycle@example.test", first_name="Life", last_name="Cycle", password="temporary-password", role=role, actor=actor)
    deactivate_user(user, actor)
    assert not user.is_active
    activate_user(user, actor)
    assert user.is_active
    reset_user_password(user, "replacement-password", actor)
    assert user.check_password("replacement-password")
    assert user.must_change_password


def test_search_filters_by_role_status_and_department(session):
    actor = make_actor(session)
    role = Role(name="Nurse")
    department = Department(code="NURS-T", name="Nursing Test")
    session.add_all([role, department])
    session.commit()
    user = create_user(username="searchnurse", email="nurse@example.test", first_name="Search", last_name="Nurse", password="temporary-password", role=role, department_id=department.id, actor=actor)
    result = search_users(search="search", role_id=role.id, status="active", department_id=department.id)
    assert [item.id for item in result.items] == [user.id]


def test_only_super_admin_assigns_role_permissions(session):
    admin = make_actor(session)
    super_admin = make_actor(session, role_name="Super Admin", username="supermanager")
    role = Role(name="Nurse")
    permission = Permission(code="nursing.record.test", module="nursing", action="record")
    session.add_all([role, permission])
    session.commit()
    try:
        assign_permissions(role, [permission.id], admin)
        assert False, "Expected PermissionError"
    except PermissionError:
        pass
    assign_permissions(role, [permission.id], super_admin)
    assert role.permissions == [permission]


def test_user_management_routes_enforce_roles(client, session):
    make_actor(session, role_name="Doctor")
    login(client)
    assert client.get("/users").status_code == 403


def test_admin_can_create_user_through_route(client, session):
    make_actor(session)
    role = Role(name="Patient")
    session.add(role)
    session.commit()
    login(client)
    response = client.post("/users/create", data={"first_name": "Route", "last_name": "User", "username": "routeuser", "email": "route@example.test", "phone": "", "role_id": role.id, "department_id": "", "specialty_id": "", "license_number": "", "password": "temporary-password", "confirm_password": "temporary-password"})
    assert response.status_code == 302
    assert session.query(User).filter_by(username="routeuser").one()
