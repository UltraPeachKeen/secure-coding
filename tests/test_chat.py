from app.extensions import db
from app.models import ChatMessage

from .conftest import login_as, make_user


def test_global_and_direct_chat_are_separated(client, app):
    with app.app_context():
        alice = make_user("alice")
        bob = make_user("bob")
        charlie = make_user("charlie")
        db.session.add_all(
            [
                ChatMessage(sender_id=alice.id, body="전체 메시지"),
                ChatMessage(sender_id=alice.id, receiver_id=bob.id, body="비밀 메시지"),
            ]
        )
        db.session.commit()
        login_as(client, charlie)
    global_data = client.get("/chat/messages").get_json()
    assert [item["body"] for item in global_data] == ["전체 메시지"]
    direct_data = client.get("/chat/messages?with=alice").get_json()
    assert direct_data == []


def test_chat_output_escapes_xss(client, app):
    with app.app_context():
        user = make_user("talker")
        login_as(client, user)
    response = client.post("/chat/global", data={"body": "<img src=x onerror=alert(1)>"}, follow_redirects=True)
    text = response.get_data(as_text=True)
    assert "&lt;img" in text and "<img src=x" not in text

