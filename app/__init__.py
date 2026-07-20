import os
from pathlib import Path

import click
from flask import Flask, render_template
from sqlalchemy import event
from sqlalchemy.engine import Engine

from .config import Config
from .extensions import csrf, db, login_manager
from .models import Product, User


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    if not app.testing and not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY 환경변수가 필요합니다. .env.example을 참고하세요.")

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "로그인이 필요합니다."

    from .admin.routes import bp as admin_bp
    from .auth.routes import bp as auth_bp
    from .chat.routes import bp as chat_bp
    from .products.routes import bp as products_bp
    from .reports.routes import bp as reports_bp
    from .transfers.routes import bp as transfers_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(transfers_bp)
    app.register_blueprint(admin_bp)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @app.after_request
    def security_headers(response):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; script-src 'self'; object-src 'none'; "
            "base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    @app.errorhandler(500)
    def error_page(error):
        if getattr(error, "code", 500) == 500:
            db.session.rollback()
        return render_template("error.html", error=error), getattr(error, "code", 500)

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        click.echo("데이터베이스를 초기화했습니다.")

    @app.cli.command("seed-demo")
    def seed_demo_command():
        db.create_all()
        demo_password = os.getenv("DEMO_PASSWORD", "DemoPassword!234")
        accounts = [("admin", "admin"), ("alice", "user"), ("bob", "user")]
        for username, role in accounts:
            if not User.query.filter_by(username=username).first():
                user = User(username=username, role=role, balance=app.config["INITIAL_BALANCE"])
                user.set_password(demo_password)
                db.session.add(user)
        db.session.commit()
        alice = User.query.filter_by(username="alice").one()
        if not Product.query.first():
            db.session.add(Product(seller=alice, title="샘플 키보드", description="정상 작동하는 중고 키보드입니다.", price=25000))
            db.session.commit()
        click.echo("샘플 계정(admin/alice/bob)과 데이터를 생성했습니다.")
        click.echo("비밀번호는 DEMO_PASSWORD 환경변수 값입니다.")

    return app
