from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.String(500), nullable=False, default="")
    balance = db.Column(db.Integer, nullable=False, default=100_000)
    role = db.Column(db.String(16), nullable=False, default="user")
    status = db.Column(db.String(16), nullable=False, default="active")
    report_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    products = db.relationship("Product", back_populates="seller", lazy="dynamic")

    __table_args__ = (
        CheckConstraint("balance >= 0", name="balance_nonnegative"),
        CheckConstraint("role IN ('user', 'admin')", name="valid_role"),
        CheckConstraint("status IN ('active', 'dormant')", name="valid_status"),
        CheckConstraint("report_count >= 0", name="report_count_nonnegative"),
    )

    @property
    def is_active(self):
        return self.status == "active"

    @property
    def is_admin(self):
        return self.role == "admin"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.String(2000), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image_filename = db.Column(db.String(64))
    status = db.Column(db.String(16), nullable=False, default="active", index=True)
    report_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    seller = db.relationship("User", back_populates="products")

    __table_args__ = (
        CheckConstraint("price > 0 AND price <= 1000000000", name="valid_price"),
        CheckConstraint("status IN ('active', 'blocked', 'sold', 'deleted')", name="valid_status"),
        CheckConstraint("report_count >= 0", name="report_count_nonnegative"),
    )


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    body = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    target_product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="RESTRICT"), index=True)
    reason = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="pending")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    reporter = db.relationship("User", foreign_keys=[reporter_id])
    target_user = db.relationship("User", foreign_keys=[target_user_id])
    target_product = db.relationship("Product", foreign_keys=[target_product_id])

    __table_args__ = (
        CheckConstraint(
            "(target_user_id IS NOT NULL AND target_product_id IS NULL) OR "
            "(target_user_id IS NULL AND target_product_id IS NOT NULL)",
            name="exactly_one_target",
        ),
        CheckConstraint("status IN ('pending', 'resolved', 'rejected')", name="valid_status"),
        UniqueConstraint("reporter_id", "target_user_id", name="uq_reporter_target_user"),
        UniqueConstraint("reporter_id", "target_product_id", name="uq_reporter_target_product"),
    )


class Transfer(db.Model):
    __tablename__ = "transfers"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])

    __table_args__ = (
        CheckConstraint("amount > 0 AND amount <= 1000000000", name="valid_amount"),
        CheckConstraint("sender_id <> receiver_id", name="different_users"),
    )


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    action = db.Column(db.String(64), nullable=False)
    target_type = db.Column(db.String(32), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    detail = db.Column(db.String(500), nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    actor = db.relationship("User")
