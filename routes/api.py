from datetime import datetime
from collections import defaultdict

from flask import Blueprint
from flask import jsonify
from flask import request

from extensions.db import db

from models.book import Book
from models.cost import Cost


api_bp = Blueprint("api", __name__)


# =========================
# 状態定数
# =========================

STATUS_LISTING = "出品中"
STATUS_SOLD = "売却済"


# =========================
# 一覧取得
# =========================
@api_bp.route("/books", methods=["GET"])
def get_books():

    books = Book.query.order_by(
        Book.created_at.desc()
    ).all()

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

        purchase_price=int(
            data.get("purchase_price") or 0
        ),

        purchase_store=data.get(
            "purchase_store"
        ),

        purchase_date=datetime.strptime(
            data.get("purchase_date"),
            "%Y-%m-%d"
        ),

        # 新規登録時は出品中
        status=STATUS_LISTING

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
# 販売更新
# =========================
@api_bp.route(
    "/books/<int:book_id>/sale",
    methods=["PATCH"]
)
def update_sale(book_id):

    book = Book.query.get_or_404(book_id)

    data = request.json

    # =========================
    # 数値
    # =========================

    sale_price = int(
        data.get("sale_price") or 0
    )

    book.sale_price = sale_price

    book.fee = int(
        data.get("fee") or 0
    )

    book.shipping_cost = int(
        data.get("shipping_cost") or 0
    )

    # =========================
    # 販売日
    # =========================

    sale_date = data.get("sale_date")

    if sale_date:

        book.sale_date = datetime.strptime(
            sale_date,
            "%Y-%m-%d"
        )

    elif sale_price > 0:

        # 自動で今日の日付
        book.sale_date = datetime.now()

    else:

        # 販売解除時
        book.sale_date = None

    # =========================
    # 配送方法
    # =========================

    book.shipping_method = data.get(
        "shipping_method"
    )

    # =========================
    # 状態自動判定
    # =========================

    if sale_price > 0:

        book.status = STATUS_SOLD

    else:

        book.status = STATUS_LISTING

    db.session.commit()

    return jsonify({
        "message": "sale updated"
    })


# =========================
# 分析サマリー
# =========================
@api_bp.route("/analytics/summary")
def analytics_summary():

    books = Book.query.all()

    total_purchase = sum(
        b.purchase_price or 0
        for b in books
    )

    total_sales = sum(
        b.sale_price or 0
        for b in books
    )

    total_fee = sum(
        b.fee or 0
        for b in books
    )

    total_shipping = sum(
        b.shipping_cost or 0
        for b in books
    )

    total_costs = sum(
        c.amount or 0
        for c in Cost.query.all()
    )

    profit = (
        total_sales
        - total_purchase
        - total_fee
        - total_shipping
        - total_costs
    )

    return jsonify({

        "purchase":
            total_purchase,

        "sales":
            total_sales,

        "fees":
            total_fee,

        "shipping":
            total_shipping,

        "costs":
            total_costs,

        "profit":
            profit,

        "inventory_count":
            len([
                b for b in books
                if b.status != STATUS_SOLD
            ]),

        "sold_count":
            len([
                b for b in books
                if b.status == STATUS_SOLD
            ])

    })


# =========================
# 月別分析
# =========================
@api_bp.route("/analytics/monthly")
def analytics_monthly():

    books = Book.query.all()
    costs = Cost.query.all()

    monthly_sales = defaultdict(int)
    monthly_profit = defaultdict(int)
    monthly_costs = defaultdict(int)

    # =========================
    # 売上・利益
    # =========================

    for book in books:

        if (
            book.sale_date
            and book.status == STATUS_SOLD
        ):

            month = book.sale_date.strftime(
                "%Y-%m"
            )

            sale_price = (
                book.sale_price or 0
            )

            purchase_price = (
                book.purchase_price or 0
            )

            fee = (
                book.fee or 0
            )

            shipping = (
                book.shipping_cost or 0
            )

            profit = (
                sale_price
                - purchase_price
                - fee
                - shipping
            )

            monthly_sales[month] += (
                sale_price
            )

            monthly_profit[month] += (
                profit
            )

    # =========================
    # 経費
    # =========================

    for cost in costs:

        month = cost.cost_date.strftime(
            "%Y-%m"
        )

        monthly_costs[month] += (
            cost.amount or 0
        )

    # =========================
    # 月一覧統合
    # =========================

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

    books = Book.query.all()

    genre_profit = defaultdict(int)

    for book in books:

        if book.status != STATUS_SOLD:
            continue

        genre = (
            book.genre
            or "未分類"
        )

        profit = (

            (book.sale_price or 0)

            -

            (book.purchase_price or 0)

            -

            (book.fee or 0)

            -

            (book.shipping_cost or 0)

        )

        genre_profit[genre] += profit

    labels = list(
        genre_profit.keys()
    )

    values = list(
        genre_profit.values()
    )

    return jsonify({

        "labels": labels,
        "values": values

    })


# =========================
# 在庫状態分析
# =========================
@api_bp.route("/analytics/status")
def analytics_status():

    books = Book.query.all()

    inventory = 0
    sold = 0

    for book in books:

        if book.status == STATUS_SOLD:

            sold += 1

        else:

            inventory += 1

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
# 回転率分析
# =========================
@api_bp.route("/analytics/rotation")
def analytics_rotation():

    books = Book.query.all()

    labels = []
    values = []

    for book in books:

        if (
            book.purchase_date
            and book.sale_date
            and book.status == STATUS_SOLD
        ):

            days = (
                book.sale_date
                -
                book.purchase_date
            ).days

            labels.append(
                (book.title or "")[:20]
            )

            values.append(days)

    return jsonify({

        "labels": labels,
        "values": values

    })


# =========================
# 利益率ランキング
# =========================
@api_bp.route("/analytics/profit-ranking")
def analytics_profit_ranking():

    books = Book.query.all()

    ranking = []

    for book in books:

        if (
            book.status != STATUS_SOLD
            or not book.purchase_price
        ):
            continue

        profit = (

            (book.sale_price or 0)

            -

            (book.purchase_price or 0)

            -

            (book.fee or 0)

            -

            (book.shipping_cost or 0)

        )

        rate = (
            profit
            / book.purchase_price
        ) * 100

        ranking.append({

            "title":
                book.title,

            "rate":
                round(rate, 1),

            "profit":
                profit

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

        cost_date=datetime.strptime(
            data.get("cost_date"),
            "%Y-%m-%d"
        ).date()

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