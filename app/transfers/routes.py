from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user
from sqlalchemy import or_, update
from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db
from ..forms import TransferForm
from ..models import Transfer, User
from ..security import active_required


bp = Blueprint("transfers", __name__, url_prefix="/transfers")


@bp.route("", methods=["GET", "POST"])
@active_required
def index():
    form = TransferForm()
    if form.validate_on_submit():
        receiver = User.query.filter_by(username=form.receiver.data).first()
        amount = form.amount.data
        if not receiver or receiver.status != "active":
            flash("송금할 수 없는 사용자입니다.", "danger")
        elif receiver.id == current_user.id:
            flash("자기 자신에게 송금할 수 없습니다.", "danger")
        else:
            try:
                result = db.session.execute(
                    update(User)
                    .where(User.id == current_user.id, User.status == "active", User.balance >= amount)
                    .values(balance=User.balance - amount)
                )
                if result.rowcount != 1:
                    db.session.rollback()
                    flash("잔액이 부족합니다.", "danger")
                else:
                    receiver_result = db.session.execute(
                        update(User).where(User.id == receiver.id, User.status == "active").values(balance=User.balance + amount)
                    )
                    if receiver_result.rowcount != 1:
                        db.session.rollback()
                        flash("송금 처리 중 상대방 상태가 변경되어 취소했습니다.", "danger")
                    else:
                        db.session.add(Transfer(sender_id=current_user.id, receiver_id=receiver.id, amount=amount))
                        db.session.commit()
                        flash(f"{receiver.username}님에게 {amount:,}원을 송금했습니다.", "success")
                        return redirect(url_for("transfers.index"))
            except SQLAlchemyError:
                db.session.rollback()
                flash("송금을 처리하지 못했습니다. 잔액은 변경되지 않았습니다.", "danger")
    history = (
        Transfer.query.filter(or_(Transfer.sender_id == current_user.id, Transfer.receiver_id == current_user.id))
        .order_by(Transfer.created_at.desc())
        .limit(100)
        .all()
    )
    return render_template("transfers/index.html", form=form, history=history)
