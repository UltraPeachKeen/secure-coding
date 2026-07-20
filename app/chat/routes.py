from flask import Blueprint, abort, jsonify, render_template
from flask_login import current_user
from sqlalchemy import and_, or_

from ..extensions import db
from ..forms import ChatForm
from ..models import ChatMessage, User
from ..security import active_required


bp = Blueprint("chat", __name__, url_prefix="/chat")


def serialize(message):
    return {
        "id": message.id,
        "sender": message.sender.username,
        "body": message.body,
        "created_at": message.created_at.isoformat(),
    }


@bp.route("/global", methods=["GET", "POST"])
@active_required
def global_chat():
    form = ChatForm()
    if form.validate_on_submit():
        db.session.add(ChatMessage(sender_id=current_user.id, body=form.body.data.strip()))
        db.session.commit()
        form.body.data = ""
    messages = ChatMessage.query.filter_by(receiver_id=None).order_by(ChatMessage.id.desc()).limit(100).all()
    return render_template("chat/chat.html", form=form, messages=list(reversed(messages)), peer=None)


@bp.route("/with/<username>", methods=["GET", "POST"])
@active_required
def direct_chat(username):
    peer = User.query.filter_by(username=username).first_or_404()
    if peer.id == current_user.id:
        abort(400)
    form = ChatForm()
    if form.validate_on_submit():
        if peer.status != "active":
            abort(400)
        db.session.add(ChatMessage(sender_id=current_user.id, receiver_id=peer.id, body=form.body.data.strip()))
        db.session.commit()
        form.body.data = ""
    messages = (
        ChatMessage.query.filter(
            or_(
                and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == peer.id),
                and_(ChatMessage.sender_id == peer.id, ChatMessage.receiver_id == current_user.id),
            )
        )
        .order_by(ChatMessage.id.desc())
        .limit(100)
        .all()
    )
    return render_template("chat/chat.html", form=form, messages=list(reversed(messages)), peer=peer)


@bp.get("/messages")
@active_required
def messages_api():
    from flask import request

    after = request.args.get("after", 0, type=int)
    username = request.args.get("with", "", type=str)[:32]
    query = ChatMessage.query.filter(ChatMessage.id > max(after, 0))
    if username:
        peer = User.query.filter_by(username=username).first_or_404()
        query = query.filter(
            or_(
                and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == peer.id),
                and_(ChatMessage.sender_id == peer.id, ChatMessage.receiver_id == current_user.id),
            )
        )
    else:
        query = query.filter(ChatMessage.receiver_id.is_(None))
    return jsonify([serialize(message) for message in query.order_by(ChatMessage.id).limit(100).all()])

