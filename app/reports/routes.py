from flask import Blueprint, abort, current_app, flash, redirect, render_template, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..forms import ReportForm
from ..models import Product, Report, User
from ..security import active_required


bp = Blueprint("reports", __name__, url_prefix="/reports")


def persist_report(report, target):
    db.session.add(report)
    try:
        db.session.flush()
        if report.target_user_id:
            count = Report.query.filter(
                Report.target_user_id == report.target_user_id,
                Report.status != "rejected",
            ).count()
        else:
            count = Report.query.filter(
                Report.target_product_id == report.target_product_id,
                Report.status != "rejected",
            ).count()
        target.report_count = count
        if count >= current_app.config["REPORT_THRESHOLD"]:
            if isinstance(target, User):
                target.status = "dormant"
            else:
                target.status = "blocked"
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return False
    return True


@bp.route("/user/<int:user_id>", methods=["GET", "POST"])
@active_required
def report_user(user_id):
    target = db.get_or_404(User, user_id)
    if target.id == current_user.id or target.is_admin:
        abort(400)
    form = ReportForm()
    if form.validate_on_submit():
        report = Report(reporter_id=current_user.id, target_user_id=target.id, reason=form.reason.data.strip())
        if not persist_report(report, target):
            flash("이미 신고한 사용자입니다.", "warning")
        else:
            flash("사용자 신고를 접수했습니다.", "success")
        return redirect(url_for("auth.profile", username=target.username))
    return render_template("reports/form.html", form=form, target_label=f"사용자 {target.username}")


@bp.route("/product/<int:product_id>", methods=["GET", "POST"])
@active_required
def report_product(product_id):
    target = db.get_or_404(Product, product_id)
    if target.seller_id == current_user.id:
        abort(400)
    form = ReportForm()
    if form.validate_on_submit():
        report = Report(reporter_id=current_user.id, target_product_id=target.id, reason=form.reason.data.strip())
        if not persist_report(report, target):
            flash("이미 신고한 상품입니다.", "warning")
        else:
            flash("상품 신고를 접수했습니다.", "success")
        if target.status == "blocked":
            return redirect(url_for("products.index"))
        return redirect(url_for("products.detail", product_id=target.id))
    return render_template("reports/form.html", form=form, target_label=f"상품 {target.title}")
