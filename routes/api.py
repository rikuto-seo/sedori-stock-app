from datetime import datetime
from collections import defaultdict

from flask import Blueprint
from flask import jsonify
from flask import request

from sqlalchemy.orm import joinedload

from extensions.db import db

from models.book import Book
from models.cost import Cost
from models.sale import Sale

from sqlalchemy import func


api_bp = Blueprint("api", __name__)


# =========================
# 状態定数
# =========================

STATUS_LISTING = "出品中"
STATUS_SOLD = "売却済"


# =========================
# 共通関数
# =========================


def parse_date(date_str):

    if not date_str:
        return None

    try:

        return datetime.strptime(
            date_str,
            "%Y-%m-%d"
        ).date()

    except:

        return None


# =========================
# 一覧取得
# =========================


@api_bp.route("/books", methods=["GET"])
def get_books():

    books = (
        Book.query
        .options(joinedload(Book.sale))
        .order_by(Book.created_at.desc())
        .all()
    )

    return jsonify([
        book.to_dict()
        for book in books
    ])


# =========================
# 新規登録
# =========================


@api_bp.route("/books", methods=["POST"])
def create_book():

    data = request.json

    book = Book(

        title=data.get("title"),

        isbn=data.get("isbn"),

        c_code=data.get("c_code"),

        genre=data.get("genre"),

        publisher=data.get("publisher"),

        book_format=data.get("book_format"),

        target=data.get("target"),

        purchase_price=int(
            data.get("purchase_price") or 0
        ),

        purchase_store=data.get(
            "purchase_store"
        ),

        purchase_date=parse_date(
            data.get("purchase_date")
        ),

        status=STATUS_LISTING,

        memo=data.get("memo")

    )

    db.session.add(book)

    db.session.commit()

    return jsonify({
        "message": "created"
    })


# =========================
# 編集
# =========================


@api_bp.route(
    "/books/<int:book_id>",
    methods=["PUT"]
)
def update_book(book_id):

    book = Book.query.get_or_404(book_id)

    data = request.json

    book.title = data.get(
        "title",
        book.title
    )

    book.isbn = data.get(
        "isbn",
        book.isbn
    )

    book.publisher = data.get(
        "publisher",
        book.publisher
    )

    book.genre = data.get(
        "genre",
        book.genre
    )

    book.book_format = data.get(
        "book_format",
        book.book_format
    )

    book.target = data.get(
        "target",
        book.target
    )

    book.purchase_price = int(
        data.get(
            "purchase_price",
            book.purchase_price
        ) or 0
    )

    book.purchase_store = data.get(
        "purchase_store",
        book.purchase_store
    )

    book.c_code = data.get(
        "c_code",
        book.c_code
    )

    book.memo = data.get(
        "memo",
        book.memo
    )

    db.session.commit()

    return jsonify({
        "message": "updated"
    })


# =========================
# 単品販売更新
# =========================


@api_bp.route(
    "/books/<int:book_id>/sale",
    methods=["PATCH"]
)
def update_sale(book_id):

    book = Book.query.get_or_404(book_id)

    data = request.json

    sale_price = int(
        data.get("sale_price") or 0
    )

    fee = int(
        data.get("fee") or 0
    )

    shipping_cost = int(
        data.get("shipping_cost") or 0
    )

    shipping_method = data.get(
        "shipping_method"
    )

    sale_date = parse_date(
        data.get("sale_date")
    )

    if sale_price > 0:

        sale = Sale(
            sale_price=sale_price,
            fee=fee,
            shipping_cost=shipping_cost,
            shipping_method=shipping_method,
            sale_date=sale_date or datetime.now().date(),
            status=STATUS_SOLD,
            book_count=1
        )

        db.session.add(sale)

        db.session.flush()

        book.sale_id = sale.id
        book.status = STATUS_SOLD

    else:

        book.sale_id = None
        book.status = STATUS_LISTING

    db.session.commit()

    return jsonify({
        "message": "sale updated"
    })


# =========================
# セット販売
# =========================


@api_bp.route(
    "/sales/group",
    methods=["POST"]
)
def create_group_sale():

    data = request.json

    book_ids = data.get("book_ids", [])

    if not book_ids:

        return jsonify({
            "message": "book_ids required"
        }), 400

    sale = Sale(

        sale_price=int(
            data.get("sale_price") or 0
        ),

        fee=int(
            data.get("fee") or 0
        ),

        shipping_cost=int(
            data.get("shipping_cost") or 0
        ),

        shipping_method=data.get(
            "shipping_method"
        ),

        sale_date=parse_date(
            data.get("sale_date")
        ) or datetime.now().date(),

        status=STATUS_SOLD,

        book_count=len(book_ids)

    )

    db.session.add(sale)

    db.session.flush()

    books = Book.query.filter(
        Book.id.in_(book_ids)
    ).all()

    for book in books:

        book.sale_id = sale.id
        book.status = STATUS_SOLD

    db.session.commit()

    return jsonify({
        "message": "group sale created",
        "sale_id": sale.id
    })


# =========================
# 分析サマリー
# =========================

@api_bp.route("/analytics/summary")
def analytics_summary():

    total_purchase = db.session.query(
        func.coalesce(func.sum(Book.purchase_price), 0)
    ).scalar()

    total_sales = db.session.query(
        func.coalesce(func.sum(Sale.sale_price), 0)
    ).scalar()

    total_fee = db.session.query(
        func.coalesce(func.sum(Sale.fee), 0)
    ).scalar()

    total_shipping = db.session.query(
        func.coalesce(func.sum(Sale.shipping_cost), 0)
    ).scalar()

    total_costs = db.session.query(
        func.coalesce(func.sum(Cost.amount), 0)
    ).scalar()

    profit = (
        total_sales
        - total_purchase
        - total_fee
        - total_shipping
        - total_costs
    )

    sold_count = db.session.query(Book).filter_by(
        status=STATUS_SOLD
    ).count()

    inventory_count = db.session.query(Book).filter(
        Book.status != STATUS_SOLD
    ).count()

    profit_rate = round((profit / total_sales) * 100, 1) if total_sales else 0

    return jsonify({
        "purchase": total_purchase,
        "sales": total_sales,
        "fees": total_fee,
        "shipping": total_shipping,
        "costs": total_costs,
        "profit": profit,
        "profit_rate": profit_rate,
        "inventory_count": inventory_count,
        "sold_count": sold_count
    })

# =========================
# 月別分析
# =========================


@api_bp.route("/analytics/monthly")
def analytics_monthly():

    from sqlalchemy import func

    sales = db.session.query(
        func.to_char(Sale.sale_date, 'YYYY-MM').label("month"),
        func.sum(Sale.sale_price).label("sales"),
        func.sum(Sale.fee).label("fees"),
        func.sum(Sale.shipping_cost).label("shipping")
    ).filter(
        Sale.sale_date != None   # ← これ追加
    ).group_by("month").all()

    costs = db.session.query(
        func.to_char(Cost.cost_date, 'YYYY-MM').label("month"),
        func.sum(Cost.amount)
    ).filter(
        Cost.cost_date != None   # ← これも追加
    ).group_by("month").all()

    sales_dict = {
        s.month: s.sales
        for s in sales
    }

    profit_dict = {
        s.month: (s.sales - s.fees - s.shipping)
        for s in sales
    }

    cost_dict = {
        c[0]: c[1]
        for c in costs
    }

    all_months = sorted(set(sales_dict) | set(cost_dict))

    return jsonify({
        "labels": all_months,
        "sales": [sales_dict.get(m, 0) for m in all_months],
        "profit": [profit_dict.get(m, 0) for m in all_months],
        "costs": [cost_dict.get(m, 0) for m in all_months]
    })

# =========================
# ジャンル利益
# =========================


@api_bp.route("/analytics/genre-profit")
def analytics_genre_profit():

    from sqlalchemy import func

    results = db.session.query(
        Book.genre,
        func.sum(
            (Sale.sale_price / func.nullif(Sale.book_count, 0))
            - (Sale.fee / func.nullif(Sale.book_count, 0))
            - (Sale.shipping_cost / func.nullif(Sale.book_count, 0))
            - Book.purchase_price
        )
    ).join(Sale).filter(
        Book.status == STATUS_SOLD
    ).group_by(Book.genre).all()

    return jsonify({
        "labels": [r[0] or "未分類" for r in results],
        "values": [round(r[1]) for r in results]
    })

# =========================
# 在庫状態分析
# =========================


@api_bp.route("/analytics/status")
def analytics_status():

    inventory = db.session.query(Book).filter(
        Book.status != STATUS_SOLD
    ).count()

    sold = db.session.query(Book).filter_by(
        status=STATUS_SOLD
    ).count()

    return jsonify({
        "labels": ["在庫", "売却済"],
        "values": [inventory, sold]
    })

# =========================
# 回転日数統計
# =========================
@api_bp.route("/analytics/rotation")
def analytics_rotation():

    from sqlalchemy import func

    avg_days = db.session.query(
        func.avg(
            func.date_part(
                'day',
                Sale.sale_date - Book.purchase_date
            )
        )
    ).join(Book).filter(
        Book.status == STATUS_SOLD
    ).scalar() or 0

    return jsonify({
        "average": round(avg_days, 1),
        "max": 0,
        "min": 0,
        "median": 0
    })

# =========================
# 利益率ランキング
# =========================


@api_bp.route("/analytics/profit-ranking")
def analytics_profit_ranking():

    books = (
        Book.query
        .options(joinedload(Book.sale))
        .filter_by(status=STATUS_SOLD)
        .all()
    )

    ranking = []

    for book in books:

        if (
            not book.purchase_price
            or not book.sale
        ):
            continue

        sale = book.sale

        book_count = sale.book_count or 1

        if book_count <= 0:
            continue

        profit = (
            ((sale.sale_price or 0) / book_count)
            -
            ((sale.fee or 0) / book_count)
            -
            ((sale.shipping_cost or 0) / book_count)
            -
            (book.purchase_price or 0)
        )

        rate = (
            profit
            / book.purchase_price
        ) * 100

        ranking.append({

            "title": book.title,

            "rate": round(rate, 1),

            "profit": round(profit)

        })

    ranking = sorted(
        ranking,
        key=lambda x: x["rate"],
        reverse=True
    )[:10]

    return jsonify(ranking)


# =========================
# 経費削除
# =========================


@api_bp.route(
    "/costs/<int:cost_id>",
    methods=["DELETE"]
)
def delete_cost(cost_id):

    cost = Cost.query.get_or_404(
        cost_id
    )

    db.session.delete(cost)

    db.session.commit()

    return jsonify({
        "message": "deleted"
    })


# =========================
# 本削除
# =========================


@api_bp.route(
    "/books/<int:book_id>",
    methods=["DELETE"]
)
def delete_book(book_id):

    book = Book.query.get_or_404(book_id)

    db.session.delete(book)

    db.session.commit()

    return jsonify({
        "message": "deleted"
    })


# =========================
# 経費登録
# =========================


@api_bp.route("/costs", methods=["POST"])
def create_cost():

    data = request.json

    cost = Cost(

        cost_type=data.get("cost_type"),

        name=data.get("name"),

        amount=int(
            data.get("amount", 0)
        ),

        quantity=int(
            data.get("quantity") or 0
        ),

        memo=data.get("memo"),

        cost_date=parse_date(
            data.get("cost_date")
        )

    )

    db.session.add(cost)

    db.session.commit()

    return jsonify({
        "message": "created"
    })


# =========================
# 経費一覧
# =========================


@api_bp.route("/costs", methods=["GET"])
def get_costs():

    costs = Cost.query.order_by(
        Cost.cost_date.desc()
    ).all()

    return jsonify([
        cost.to_dict()
        for cost in costs
    ])
