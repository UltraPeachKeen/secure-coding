from app.extensions import db
from app.models import Transfer, User

from .conftest import login_as, make_user


def test_valid_transfer_updates_both_balances_and_history(client, app):
    with app.app_context():
        sender = make_user("sender", balance=100_000)
        receiver = make_user("receiver", balance=10_000)
        sender_id, receiver_id = sender.id, receiver.id
        login_as(client, sender)
    response = client.post("/transfers", data={"receiver": "receiver", "amount": 25000}, follow_redirects=True)
    assert "25,000원을 송금" in response.get_data(as_text=True)
    with app.app_context():
        assert db.session.get(User, sender_id).balance == 75_000
        assert db.session.get(User, receiver_id).balance == 35_000
        assert Transfer.query.one().amount == 25_000


def test_invalid_transfers_do_not_change_balance(client, app):
    with app.app_context():
        sender = make_user("sender", balance=1000)
        make_user("receiver", balance=1000)
        sender_id = sender.id
        login_as(client, sender)
    for receiver, amount in [("sender", 100), ("receiver", 0), ("receiver", -1), ("receiver", 2000)]:
        client.post("/transfers", data={"receiver": receiver, "amount": amount})
    with app.app_context():
        assert db.session.get(User, sender_id).balance == 1000
        assert Transfer.query.count() == 0


def test_transfer_to_dormant_user_is_rejected(client, app):
    with app.app_context():
        sender = make_user("sender", balance=1000)
        make_user("sleeping_receiver", balance=1000, status="dormant")
        sender_id = sender.id
        login_as(client, sender)
    client.post("/transfers", data={"receiver": "sleeping_receiver", "amount": 100})
    with app.app_context():
        assert db.session.get(User, sender_id).balance == 1000
        assert Transfer.query.count() == 0
