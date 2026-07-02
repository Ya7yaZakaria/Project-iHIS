def test_application_factory(app):
    assert app.config["TESTING"] is True
    expected = {
        "auth", "patients", "doctors", "emr", "laboratory", "radiology",
        "pharmacy", "dentistry", "rehabilitation", "womens_health",
    }
    assert expected.issubset(app.blueprints)


def test_dashboard_renders(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_not_found_handler(client):
    response = client.get("/not-a-real-page")
    assert response.status_code == 404
    assert b"Page not found" in response.data


def test_internal_error_handler(client):
    response = client.get("/_test/error")
    assert response.status_code == 500
    assert b"Something went wrong" in response.data
