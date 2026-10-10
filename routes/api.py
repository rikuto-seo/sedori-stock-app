from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload
from extensions.db import db
from models.book import Book
from models.cost import Cost
from models.sale import Sale
from services.isbn import normalize_isbn

api_bp = Blueprint("api", __name__)
STATUS_LISTING = "出品中"
STATUS_SOLD = "売却済"


def today():
    return datetime.now(timezone(timedelta(hours=9))).date()


def parse_date(value, default=None):
    if not value:
        return default
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError("日付はYYYY-MM-DD形式で入力してください")


def integer(value, name, minimum=0):
    if isinstance(value, bool):
        raise ValueError(f"{name}は整数で入力してください")
    try:
        result = int(str(value if value is not None and value != "" else 0))
    except (ValueError, TypeError):
        raise ValueError(f"{name}は整数で入力してください")
    if minimum is not None and result < minimum:
        raise ValueError(f"{name}は{minimum}以上で入力してください")
    if abs(result) > 2_147_483_647:
        raise ValueError(f"{name}の値が大きすぎます")
    return result


def payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("入力データを確認してください")
    return data


@api_bp.errorhandler(ValueError)
def invalid(error):
    db.session.rollback()
    return jsonify(message=str(error)), 400


def book_values(data):
    if not isinstance(data, dict):
        raise ValueError("本の入力データを確認してください")
    title = str(data.get("title") or "").strip()
    if not title or len(title) > 255:
        raise ValueError("タイトルは1〜255文字で入力してください")
    isbn = normalize_isbn(data["isbn"]) if data.get("isbn") else None
    result = {"title": title, "isbn": isbn,
              "purchase_price": integer(data.get("purchase_price"), "仕入れ値"),
              "purchase_date": parse_date(data.get("purchase_date"), today())}
    for key, limit in (("c_code",20),("publisher",100),("genre",100),("book_format",50),
                       ("target",50),("purchase_store",100),("memo",10000)):
        value = str(data.get(key) or "").strip()
        if len(value) > limit:
            raise ValueError(f"{key}は{limit}文字以内で入力してください")
        result[key] = value
    return result


@api_bp.get("/books")
def get_books():
    books = Book.query.options(joinedload(Book.sale)).order_by(Book.created_at.desc(), Book.id.desc()).all()
    return jsonify([book.to_dict() for book in books])


@api_bp.post("/books")
def create_book():
    book = Book(**book_values(payload()), status=STATUS_LISTING)
    db.session.add(book)
    db.session.commit()
    return jsonify(message="created", id=book.id), 201


@api_bp.post("/books/batch")
def create_books():
    data = payload()
    entries = data.get("books")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 200:
        raise ValueError("1〜200冊をまとめて登録できます")
    # Validate every row before writing; one failed row must not partially save a purchase.
    values = [book_values(entry) for entry in entries]
    books = [Book(**entry, status=STATUS_LISTING) for entry in values]
    db.session.add_all(books)
    db.session.commit()
    return jsonify(message="created", count=len(books), ids=[book.id for book in books]), 201


@api_bp.put("/books/<int:book_id>")
def update_book(book_id):
    book = db.get_or_404(Book, book_id)
    data = book.to_dict()
    data.update(payload())
    for key, value in book_values(data).items():
        setattr(book, key, value)
    db.session.commit()
    return jsonify(message="updated")


def sale_values(data):
    return {"sale_price": integer(data.get("sale_price"), "販売価格"),
            "fee": integer(data.get("fee"), "手数料"),
            "shipping_cost": integer(data.get("shipping_cost"), "送料"),
            "shipping_method": str(data.get("shipping_method") or "")[:100],
            "sale_date": datetime.combine(parse_date(data.get("sale_date"), today()), datetime.min.time())}


@api_bp.patch("/books/<int:book_id>/sale")
def update_sale(book_id):
    book = db.get_or_404(Book, book_id)
    values = sale_values(payload())
    if book.sale and book.sale.book_count > 1:
        return jsonify(message="セット販売済みの本は単品販売で変更できません"), 409
    old_sale = book.sale
    if values["sale_price"] > 0:
        sale = old_sale or Sale(book_count=1, status=STATUS_SOLD)
        for key, value in values.items():
            setattr(sale, key, value)
        db.session.add(sale)
        book.sale = sale
        book.status = STATUS_SOLD
    else:
        book.sale = None
        book.status = STATUS_LISTING
        if old_sale:
            db.session.delete(old_sale)
    db.session.commit()
    return jsonify(message="sale updated")


@api_bp.post("/sales/group")
def create_group_sale():
    data = payload()
    ids = data.get("book_ids")
    if not isinstance(ids, list) or not ids or len(ids) > 200:
        raise ValueError("販売する本を選択してください")
    ids = [integer(value, "本のID", 1) for value in ids]
    if len(set(ids)) != len(ids):
        raise ValueError("同じ本が重複しています")
    books = Book.query.filter(Book.id.in_(ids)).all()
    if len(books) != len(ids) or any(b.sale_id or b.status == STATUS_SOLD for b in books):
        return jsonify(message="選択した本が見つからないか、すでに売却済みです"), 409
    values = sale_values(data)
    if not values["sale_price"]:
        raise ValueError("販売価格は1円以上で入力してください")
    sale = Sale(**values, status=STATUS_SOLD, book_count=len(books))
    db.session.add(sale)
    for book in books:
        book.sale = sale
        book.status = STATUS_SOLD
    db.session.commit()
    return jsonify(message="group sale created", sale_id=sale.id), 201


@api_bp.delete("/books/<int:book_id>")
def delete_book(book_id):
    book = db.get_or_404(Book, book_id)
    if book.sale_id:
        return jsonify(message="売却済みの本は販売記録を戻してから削除してください"), 409
    db.session.delete(book)
    db.session.commit()
    return jsonify(message="deleted")


@api_bp.post("/costs")
def create_cost():
    data = payload()
    kind = data.get("cost_type")
    name = str(data.get("name") or "").strip()
    if kind not in ("packaging", "material", "coupon") or not name or len(name) > 100:
        raise ValueError("経費の種類と名称を確認してください")
    amount = integer(data.get("amount"), "金額", None if kind == "coupon" else 0)
    if kind == "coupon":
        amount = -abs(amount)
    cost = Cost(cost_type=kind, name=name, amount=amount,
                quantity=integer(data.get("quantity"), "数量"), memo=data.get("memo"),
                cost_date=parse_date(data.get("cost_date"), today()))
    db.session.add(cost)
    db.session.commit()
    return jsonify(message="created", id=cost.id), 201


@api_bp.get("/costs")
def get_costs():
    return jsonify([cost.to_dict() for cost in Cost.query.order_by(Cost.cost_date.desc()).all()])


@api_bp.delete("/costs/<int:cost_id>")
def delete_cost(cost_id):
    db.session.delete(db.get_or_404(Cost, cost_id))
    db.session.commit()
    return jsonify(message="deleted")
