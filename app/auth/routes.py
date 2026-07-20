from urllib.parse import urljoin, urlparse

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..forms import LoginForm, PasswordChangeForm, ProfileForm, RegisterForm
from ..models import User
from ..security import active_required


bp = Blueprint("auth", __name__)


def is_safe_redirect(target):
    host = urlparse(request.host_url)
    destination = urlparse(urljoin(request.host_url, target))
    return destination.scheme in ("http", "https") and host.netloc == destination.netloc


@bp.route("/auth/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("products.index"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, balance=current_app.config["INITIAL_BALANCE"])
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("가입이 완료되었습니다. 로그인해 주세요.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@bp.route("/auth/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("products.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.status == "active" and user.check_password(form.password.data):
            login_user(user)
            destination = request.args.get("next")
            if destination and is_safe_redirect(destination):
                return redirect(destination)
            return redirect(url_for("products.index"))
        flash("아이디 또는 비밀번호가 올바르지 않거나 사용할 수 없는 계정입니다.", "danger")
    return render_template("auth/login.html", form=form)


@bp.post("/auth/logout")
@login_required
def logout():
    logout_user()
    flash("로그아웃했습니다.", "info")
    return redirect(url_for("products.index"))


@bp.get("/users/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("auth/profile.html", profile_user=user)


@bp.get("/account")
@login_required
def account():
    return render_template("auth/account.html")


@bp.route("/account/profile", methods=["GET", "POST"])
@active_required
def edit_profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.bio = form.bio.data.strip()
        db.session.commit()
        flash("소개글을 수정했습니다.", "success")
        return redirect(url_for("auth.account"))
    return render_template("auth/edit_profile.html", form=form)


@bp.route("/account/password", methods=["GET", "POST"])
@active_required
def change_password():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("현재 비밀번호가 올바르지 않습니다.", "danger")
        elif current_user.check_password(form.new_password.data):
            flash("새 비밀번호는 현재 비밀번호와 달라야 합니다.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            logout_user()
            flash("비밀번호를 변경했습니다. 다시 로그인해 주세요.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/change_password.html", form=form)
