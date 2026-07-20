from app.extensions import db
from app.models import User

from .conftest import login_as, make_user


def test_register_hashes_password(client, app):
    response = client.post(
        "/auth/register",
        data={"username": "new_user", "password": "VeryStrong!123", "confirm": "VeryStrong!123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username="new_user").one()
        assert user.password_hash != "VeryStrong!123"
        assert user.check_password("VeryStrong!123")


def test_login_uses_generic_error_and_rejects_dormant(client, app):
    with app.app_context():
        make_user("sleeping", status="dormant")
    response = client.post("/auth/login", data={"username": "sleeping", "password": "StrongPassword!1"})
    assert "사용할 수 없는 계정" in response.get_data(as_text=True)
    response = client.post("/auth/login", data={"username": "missing", "password": "StrongPassword!1"})
    assert "아이디 또는 비밀번호" in response.get_data(as_text=True)


def test_profile_and_password_change(client, app):
    with app.app_context():
        user = make_user("alice")
        user_id = user.id
        login_as(client, user)
    response = client.post("/account/profile", data={"bio": "안전한 소개"}, follow_redirects=True)
    assert "안전한 소개" in response.get_data(as_text=True)
    response = client.post(
        "/account/password",
        data={"current_password": "StrongPassword!1", "new_password": "ChangedPassword!2", "confirm": "ChangedPassword!2"},
        follow_redirects=True,
    )
    assert "다시 로그인" in response.get_data(as_text=True)
    with app.app_context():
        assert db.session.get(User, user_id).check_password("ChangedPassword!2")

