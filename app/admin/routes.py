from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from ..extensions import db
from ..forms import ActionForm
from ..models import AuditLog, Product, Report, Transfer, User
from ..security import admin_required


bp = Blueprint("admin", __name__, url_prefix="/admin")


def log_action(action, target_type, target_id, detail=""):
    db.session.add(
        AuditLog(actor_id=current_user.id, action=action, target_type=target_type, target_id=target_id, detail=detail)
    )


@bp.get("")
@admin_required
def dashboard():
    counts = {
        "users": User.query.count(),
        "products": Product.query.count(),
        "reports": Report.query.count(),
        "transfers": Transfer.query.count(),
    }
    return render_template("admin/dashboard.html", counts=counts)


@bp.get("/users")
@admin_required
def users():
    return render_template("admin/users.html", users=User.query.order_by(User.id).all(), action_form=ActionForm())


@bp.post("/users/<int:user_id>/status")
@admin_required
def user_status(user_id):
    form = ActionForm()
    if not form.validate_on_submit() or form.action.data not in {"active", "dormant"}:
        abort(400)
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id and form.action.data == "dormant":
        abort(400)
    user.status = form.action.data
    log_action("user_status", "user", user.id, user.status)
    db.session.commit()
    flash("사용자 상태를 변경했습니다.", "success")
    return redirect(url_for("admin.users"))


@bp.get("/products")
@admin_required
def products():
    return render_template("admin/products.html", products=Product.query.order_by(Product.id.desc()).all(), action_form=ActionForm())


@bp.post("/products/<int:product_id>/status")
@admin_required
def product_status(product_id):
    form = ActionForm()
    if not form.validate_on_submit() or form.action.data not in {"active", "blocked"}:
        abort(400)
    product = db.get_or_404(Product, product_id)
    product.status = form.action.data
    log_action("product_status", "product", product.id, product.status)
    db.session.commit()
    flash("상품 상태를 변경했습니다.", "success")
    return redirect(url_for("admin.products"))


@bp.get("/reports")
@admin_required
def reports():
    return render_template("admin/reports.html", reports=Report.query.order_by(Report.id.desc()).all(), action_form=ActionForm())


@bp.post("/reports/<int:report_id>/status")
@admin_required
def report_status(report_id):
    form = ActionForm()
    if not form.validate_on_submit() or form.action.data not in {"resolved", "rejected"}:
        abort(400)
    report = db.get_or_404(Report, report_id)
    report.status = form.action.data
    if report.target_user_id:
        report.target_user.report_count = Report.query.filter(
            Report.target_user_id == report.target_user_id, Report.status != "rejected"
        ).count()
    else:
        report.target_product.report_count = Report.query.filter(
            Report.target_product_id == report.target_product_id, Report.status != "rejected"
        ).count()
    log_action("report_status", "report", report.id, report.status)
    db.session.commit()
    flash("신고 상태를 변경했습니다.", "success")
    return redirect(url_for("admin.reports"))


@bp.get("/transfers")
@admin_required
def transfers():
    return render_template("admin/transfers.html", transfers=Transfer.query.order_by(Transfer.id.desc()).limit(500).all())


@bp.get("/audit-logs")
@admin_required
def audit_logs():
    return render_template("admin/audit_logs.html", logs=AuditLog.query.order_by(AuditLog.id.desc()).limit(500).all())

