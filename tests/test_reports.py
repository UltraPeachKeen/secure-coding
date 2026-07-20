from app.extensions import db
from app.models import Product, Report, User

from .conftest import login_as, make_user


def test_duplicate_product_report_is_rejected(client, app):
    with app.app_context():
        seller = make_user("seller")
        reporter = make_user("reporter")
        product = Product(seller_id=seller.id, title="의심 상품", description="설명", price=1000)
        db.session.add(product)
        db.session.commit()
        product_id = product.id
        login_as(client, reporter)
    for _ in range(2):
        client.post(f"/reports/product/{product_id}", data={"reason": "충분히 구체적인 신고 사유"})
    with app.app_context():
        assert Report.query.filter_by(target_product_id=product_id).count() == 1


def test_three_reports_block_product(client, app):
    with app.app_context():
        seller = make_user("seller")
        reporters = [make_user(f"reporter{i}") for i in range(3)]
        product = Product(seller_id=seller.id, title="차단 대상", description="설명", price=1000)
        db.session.add(product)
        db.session.commit()
        product_id = product.id
        reporter_ids = [u.id for u in reporters]
    for user_id in reporter_ids:
        with app.app_context():
            username = db.session.get(User, user_id).username
        client.post("/auth/logout")
        client.post("/auth/login", data={"username": username, "password": "StrongPassword!1"})
        client.post(f"/reports/product/{product_id}", data={"reason": "반복적으로 문제가 확인된 상품"})
    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.report_count == 3
        assert product.status == "blocked"


def test_three_reports_make_user_dormant(client, app):
    with app.app_context():
        target = make_user("target")
        reporters = [make_user(f"r{i}") for i in range(3)]
        target_id = target.id
        reporter_ids = [u.id for u in reporters]
    for user_id in reporter_ids:
        with app.app_context():
            username = db.session.get(User, user_id).username
        client.post("/auth/logout")
        client.post("/auth/login", data={"username": username, "password": "StrongPassword!1"})
        client.post(f"/reports/user/{target_id}", data={"reason": "지속적인 악성 행위가 확인됨"})
    with app.app_context():
        assert db.session.get(User, target_id).status == "dormant"
