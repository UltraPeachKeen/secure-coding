import io

from app.extensions import db
from app.models import Product

from .conftest import login_as, make_user


def test_product_crud_search_and_xss_escape(client, app):
    with app.app_context():
        owner = make_user("owner")
        login_as(client, owner)
    response = client.post(
        "/products/new",
        data={"title": "키보드", "description": "<script>alert(1)</script>", "price": 30000},
        follow_redirects=True,
    )
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "&lt;script&gt;" in text and "<script>alert(1)</script>" not in text
    assert "키보드" in client.get("/?q=키보드").get_data(as_text=True)


def test_other_user_cannot_edit_or_delete(client, app):
    with app.app_context():
        owner = make_user("owner")
        attacker = make_user("attacker")
        product = Product(seller_id=owner.id, title="상품", description="설명", price=1000)
        db.session.add(product)
        db.session.commit()
        product_id = product.id
        login_as(client, attacker)
    assert client.get(f"/products/{product_id}/edit").status_code == 403
    assert client.post(f"/products/{product_id}/delete").status_code == 403


def test_upload_rejects_fake_image(client, app):
    with app.app_context():
        user = make_user("uploader")
        login_as(client, user)
    response = client.post(
        "/products/new",
        data={
            "title": "가짜 이미지",
            "description": "실행 파일 위장",
            "price": 1000,
            "image": (io.BytesIO(b"not-an-image"), "attack.png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert "유효한 이미지" in response.get_data(as_text=True)


def test_upload_rejects_disallowed_extension_even_with_image_bytes(client, app):
    from PIL import Image

    image_bytes = io.BytesIO()
    Image.new("RGB", (1, 1), "white").save(image_bytes, format="PNG")
    image_bytes.seek(0)
    with app.app_context():
        user = make_user("extension_user")
        login_as(client, user)
    response = client.post(
        "/products/new",
        data={
            "title": "확장자 위장",
            "description": "내용은 이미지지만 확장자가 잘못됨",
            "price": 1000,
            "image": (image_bytes, "image.exe"),
        },
        content_type="multipart/form-data",
    )
    assert "확장자만" in response.get_data(as_text=True)


def test_owner_soft_deletes_product(client, app):
    with app.app_context():
        owner = make_user("seller")
        product = Product(seller_id=owner.id, title="삭제 상품", description="설명", price=1000)
        db.session.add(product)
        db.session.commit()
        product_id = product.id
        login_as(client, owner)
    assert client.post(f"/products/{product_id}/delete", follow_redirects=True).status_code == 200
    with app.app_context():
        assert db.session.get(Product, product_id).status == "deleted"
