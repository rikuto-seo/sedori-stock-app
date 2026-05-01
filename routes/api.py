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
            status=STATUS_SOLD
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

        status=STATUS_SOLD

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

    books = Book.query.all()
    sales = Sale.query.all()
    costs = Cost.query.all()

    total_purchase = sum(
        b.purchase_price or 0
        for b in books
    )

    total_sales = sum(
        s.sale_price or 0
        for s in sales
    )

    total_fee = sum(
        s.fee or 0
        for s in sales
    )

    total_shipping = sum(
        s.shipping_cost or 0
        for s in sales
    )

    total_costs = sum(
        c.amount or 0
        for c in costs
    )

    profit = (
        total_sales
        - total_purchase
        - total_fee
        - total_shipping
        - total_costs
    )

    # =========================
    # 利益率
    # =========================

    if total_sales > 0:

        profit_rate = round(

            (
                profit
                / total_sales
            ) * 100,

            1

        )

    else:

        profit_rate = 0

    return jsonify({

        "purchase": total_purchase,

        "sales": total_sales,

        "fees": total_fee,

        "shipping": total_shipping,

        "costs": total_costs,

        "profit_rate": profit_rate,

        "profit": profit,

        "inventory_count": len([
            b for b in books
            if b.status != STATUS_SOLD
        ]),

        "sold_count": len([
            b for b in books
            if b.status == STATUS_SOLD
        ])

    })


# =========================
# 月別分析
# =========================


@api_bp.route("/analytics/monthly")
def analytics_monthly():

    sales = (
        Sale.query
        .options(joinedload(Sale.books))
        .all()
    )

    costs = Cost.query.all()

    monthly_sales = defaultdict(int)
    monthly_profit = defaultdict(int)
    monthly_costs = defaultdict(int)

    for sale in sales:

        if not sale.sale_date:
            continue

        month = sale.sale_date.strftime(
            "%Y-%m"
        )

        purchase_total = sum(
            b.purchase_price or 0
            for b in sale.books
        )

        sale_price = sale.sale_price or 0
        fee = sale.fee or 0
        shipping = sale.shipping_cost or 0

        profit = (
            sale_price
            - purchase_total
            - fee
            - shipping
        )

        monthly_sales[month] += sale_price
        monthly_profit[month] += profit

    for cost in costs:

        if not cost.cost_date:
            continue

        month = cost.cost_date.strftime(
            "%Y-%m"
        )

        monthly_costs[month] += (
            cost.amount or 0
        )

    all_months = sorted(set(

        list(monthly_sales.keys())
        +
        list(monthly_profit.keys())
        +
        list(monthly_costs.keys())

    ))

    return jsonify({

        "labels": all_months,

        "sales": [
            monthly_sales[m]
            for m in all_months
        ],

        "profit": [
            monthly_profit[m]
            for m in all_months
        ],

        "costs": [
            monthly_costs[m]
            for m in all_months
        ]

    })


# =========================
# ジャンル利益
# =========================


@api_bp.route("/analytics/genre-profit")
def analytics_genre_profit():

    books = (
        Book.query
        .options(joinedload(Book.sale))
        .filter_by(status=STATUS_SOLD)
        .all()
    )

    genre_profit = defaultdict(int)

    for book in books:

        if not book.sale:
            continue

        genre = book.genre or "未分類"

        sale = book.sale

        book_count = len(sale.books)

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

        genre_profit[genre] += round(profit)

    return jsonify({

        "labels": list(
            genre_profit.keys()
        ),

        "values": list(
            genre_profit.values()
        )

    })


# =========================
# 在庫状態分析
# =========================


@api_bp.route("/analytics/status")
def analytics_status():

    books = Book.query.all()

    inventory = len([
        b for b in books
        if b.status != STATUS_SOLD
    ])

    sold = len([
        b for b in books
        if b.status == STATUS_SOLD
    ])

    return jsonify({

        "labels": [
            "在庫",
            "売却済"
        ],

        "values": [
            inventory,
            sold
        ]

    })


# =========================
# 回転日数統計
# =========================
@api_bp.route("/analytics/rotation")
def analytics_rotation():

    books = Book.query.filter_by(
        status=STATUS_SOLD
    ).all()

    rotation_days = []

    for book in books:

        if (
            book.purchase_date
            and book.sale
            and book.sale.sale_date
        ):

            days = (
                book.sale.sale_date
                -
                book.purchase_date
            ).days

            if days >= 0:
                rotation_days.append(days)

    if not rotation_days:

        return jsonify({

            "average": 0,
            "max": 0,
            "min": 0,
            "median": 0

        })

    rotation_days.sort()

    count = len(rotation_days)

    average_days = round(
        sum(rotation_days) / count,
        1
    )

    max_days = max(rotation_days)

    min_days = min(rotation_days)

    # =========================
    # 中央値
    # =========================

    middle = count // 2

    if count % 2 == 0:

        median_days = round(

            (
                rotation_days[middle - 1]
                +
                rotation_days[middle]
            ) / 2,

            1

        )

    else:

        median_days = rotation_days[middle]

    return jsonify({

        "average": average_days,

        "max": max_days,

        "min": min_days,

        "median": median_days

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

        book_count = len(sale.books)

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
