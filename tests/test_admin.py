from app.extensions import db
from app.models import AuditLog, User

from .conftest import login_as, make_user


def test_regular_user_cannot_access_admin(client, app):
    with app.app_context():
        user = make_user("normal")
        login_as(client, user)
    assert client.get("/admin").status_code == 403


def test_admin_changes_user_status_and_logs_action(client, app):
    with app.app_context():
        admin = make_user("admin", role="admin")
        user = make_user("normal")
        user_id = user.id
        login_as(client, admin)
    response = client.post(f"/admin/users/{user_id}/status", data={"action": "dormant"}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(User, user_id).status == "dormant"
        assert AuditLog.query.filter_by(target_id=user_id, action="user_status").count() == 1

