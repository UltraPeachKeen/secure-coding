import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import User


@pytest.fixture()
def app(tmp_path):
    class LocalTestConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"
        UPLOAD_FOLDER = str(tmp_path / "uploads")
        SECRET_KEY = "test-secret-key"
        INITIAL_BALANCE = 100_000
        REPORT_THRESHOLD = 3

    application = create_app(LocalTestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def make_user(username, password="StrongPassword!1", **kwargs):
    user = User(username=username, **kwargs)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login_as(client, user):
    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True

