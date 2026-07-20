from pathlib import Path
from uuid import uuid4

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from PIL import Image, UnidentifiedImageError
from sqlalchemy import or_

from ..extensions import db
from ..forms import ProductForm
from ..models import Product
from ..security import active_required


bp = Blueprint("products", __name__)
ALLOWED_FORMATS = {"PNG": ".png", "JPEG": ".jpg", "GIF": ".gif", "WEBP": ".webp"}
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
Image.MAX_IMAGE_PIXELS = 25_000_000


def save_verified_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if Path(file_storage.filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("PNG, JPEG, GIF, WebP 확장자만 업로드할 수 있습니다.")
    try:
        image = Image.open(file_storage.stream)
        if image.width > 5000 or image.height > 5000:
            raise ValueError("이미지 크기는 5000x5000 이하여야 합니다.")
        image.verify()
        file_storage.stream.seek(0)
        image = Image.open(file_storage.stream)
        image.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError("유효한 이미지 파일이 아닙니다.") from exc
    if image.format not in ALLOWED_FORMATS:
        raise ValueError("PNG, JPEG, GIF, WebP 형식의 5000x5000 이하 이미지만 가능합니다.")
    filename = f"{uuid4().hex}{ALLOWED_FORMATS[image.format]}"
    destination = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    if image.format == "JPEG" and image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    image.save(destination, format=image.format)
    return filename


@bp.get("/")
def index():
    query = Product.query.filter_by(status="active")
    q = request.args.get("q", "").strip()[:100]
    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        query = query.filter(or_(Product.title.ilike(pattern, escape="\\"), Product.description.ilike(pattern, escape="\\")))
    products = query.order_by(Product.created_at.desc()).all()
    return render_template("products/index.html", products=products, q=q)


@bp.route("/products/new", methods=["GET", "POST"])
@active_required
def create():
    form = ProductForm()
    if form.validate_on_submit():
        try:
            filename = save_verified_image(form.image.data)
        except ValueError as exc:
            form.image.errors.append(str(exc))
        else:
            product = Product(
                seller_id=current_user.id,
                title=form.title.data.strip(),
                description=form.description.data.strip(),
                price=form.price.data,
                image_filename=filename,
            )
            db.session.add(product)
            db.session.commit()
            flash("상품을 등록했습니다.", "success")
            return redirect(url_for("products.detail", product_id=product.id))
    return render_template("products/form.html", form=form, heading="상품 등록")


@bp.get("/products/mine")
@login_required
def mine():
    products = Product.query.filter_by(seller_id=current_user.id).order_by(Product.created_at.desc()).all()
    return render_template("products/mine.html", products=products)


@bp.get("/products/<int:product_id>")
def detail(product_id):
    product = db.get_or_404(Product, product_id)
    if product.status != "active" and not (
        current_user.is_authenticated and (current_user.id == product.seller_id or current_user.is_admin)
    ):
        abort(404)
    return render_template("products/detail.html", product=product)


@bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@active_required
def edit(product_id):
    product = db.get_or_404(Product, product_id)
    if product.seller_id != current_user.id:
        abort(403)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        old_filename = product.image_filename
        new_filename = None
        try:
            if form.image.data and form.image.data.filename:
                new_filename = save_verified_image(form.image.data)
        except ValueError as exc:
            form.image.errors.append(str(exc))
        else:
            product.title = form.title.data.strip()
            product.description = form.description.data.strip()
            product.price = form.price.data
            if new_filename:
                product.image_filename = new_filename
            db.session.commit()
            if new_filename and old_filename:
                (Path(current_app.config["UPLOAD_FOLDER"]) / old_filename).unlink(missing_ok=True)
            flash("상품을 수정했습니다.", "success")
            return redirect(url_for("products.detail", product_id=product.id))
    return render_template("products/form.html", form=form, heading="상품 수정")


@bp.post("/products/<int:product_id>/delete")
@active_required
def delete(product_id):
    product = db.get_or_404(Product, product_id)
    if product.seller_id != current_user.id:
        abort(403)
    filename = product.image_filename
    product.status = "deleted"
    product.image_filename = None
    db.session.commit()
    if filename:
        (Path(current_app.config["UPLOAD_FOLDER"]) / filename).unlink(missing_ok=True)
    flash("상품을 삭제했습니다.", "info")
    return redirect(url_for("products.mine"))


@bp.get("/uploads/<filename>")
def uploaded_file(filename):
    product = Product.query.filter_by(image_filename=filename).first_or_404()
    if product.status != "active" and not (
        current_user.is_authenticated and (current_user.id == product.seller_id or current_user.is_admin)
    ):
        abort(404)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
