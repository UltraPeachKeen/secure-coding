from app import create_app
from app.config import TestConfig


def test_security_headers(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_csrf_rejects_missing_token(tmp_path):
    class CsrfConfig(TestConfig):
        WTF_CSRF_ENABLED = True
        SECRET_KEY = "csrf-test-secret"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'csrf.db'}"
        UPLOAD_FOLDER = str(tmp_path / "uploads")

    app = create_app(CsrfConfig)
    response = app.test_client().post(
        "/auth/register",
        data={"username": "attacker", "password": "VeryStrong!123", "confirm": "VeryStrong!123"},
    )
    assert response.status_code == 400


def test_search_payload_is_not_sql(client):
    response = client.get("/?q=' OR 1=1 --")
    assert response.status_code == 200

