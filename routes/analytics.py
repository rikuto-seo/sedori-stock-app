"""Database-side analytics, without materializing the inventory."""
from datetime import date, datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from sqlalchemy import func, case, cast, Date, Float, select
import json
from extensions.db import db
from models.book import Book
from models.sale import Sale
from models.cost import Cost

analytics_bp = Blueprint("analytics", __name__)


def month(column):
    if db.engine.dialect.name == "sqlite":
        return func.strftime("%Y-%m", column)
    return func.to_char(column, "YYYY-MM")


def sum0(column):
    return func.coalesce(func.sum(column), 0)


def day_diff(end, start):
    if db.engine.dialect.name == "sqlite":
        return func.julianday(end) - func.julianday(start)
    return cast(end, Date) - cast(start, Date)


def per_book_profit():
    divisor = cast(func.coalesce(func.nullif(Sale.book_count, 0), 1), Float)
    return ((func.coalesce(Sale.sale_price, 0) - func.coalesce(Sale.fee, 0)
             - func.coalesce(Sale.shipping_cost, 0)) / divisor - Book.purchase_price)


def queries():
    sold, inventory = Book.sale_id.isnot(None), Book.sale_id.is_(None)
    now = datetime.now(timezone(timedelta(hours=9))).date()
    sold_cost = db.session.query(Book.sale_id.label("sale_id"), sum0(Book.purchase_price).label("amount"))\
        .filter(sold).group_by(Book.sale_id).subquery()
    m, p, c = month(Sale.sale_date), month(Book.purchase_date), month(Cost.cost_date)
    profit = per_book_profit()
    days = day_diff(Sale.sale_date, Book.purchase_date)
    ordered_days = db.session.query(days.label("days"), func.row_number().over(order_by=days).label("position"),
                                    func.count().over().label("total")).select_from(Book).join(Sale)\
        .filter(Sale.sale_date.isnot(None), Book.purchase_date.isnot(None), days >= 0).subquery()
    result = {
        "books": db.session.query(sum0(Book.purchase_price), sum0(case((sold, Book.purchase_price), else_=0)),
                                  sum0(case((inventory, Book.purchase_price), else_=0)),
                                  sum0(case((sold, 1), else_=0)), sum0(case((inventory, 1), else_=0)),
                                  sum0(case((inventory & (Book.purchase_date < now - timedelta(days=90)), 1), else_=0))),
        "sales": db.session.query(sum0(Sale.sale_price), sum0(Sale.fee), sum0(Sale.shipping_cost),
                                  func.count(Sale.id)).filter(Sale.books.any()),
        "costs": db.session.query(sum0(Cost.amount)),
        "monthly_sales": db.session.query(m.label("month"), sum0(Sale.sale_price), sum0(Sale.fee),
                                           sum0(Sale.shipping_cost), sum0(sold_cost.c.amount))
                         .join(sold_cost, sold_cost.c.sale_id == Sale.id)
                         .filter(Sale.sale_date.isnot(None)).group_by(m).order_by(m),
        "monthly_purchase": db.session.query(p.label("month"), sum0(Book.purchase_price)).group_by(p).order_by(p),
        "monthly_costs": db.session.query(c.label("month"), sum0(Cost.amount)).group_by(c).order_by(c),
        "rotation": db.session.query(func.avg(days), func.min(days), func.max(days), func.count(Book.id))
                    .join(Sale).filter(Sale.sale_date.isnot(None), Book.purchase_date.isnot(None), days >= 0),
        "median": db.session.query(func.avg(ordered_days.c.days)).filter(
            ordered_days.c.position >= func.floor((ordered_days.c.total + 1) / 2),
            ordered_days.c.position <= func.floor((ordered_days.c.total + 2) / 2)),
        "ranking": db.session.query(Book.title, profit.label("profit"), Book.purchase_price)
                   .join(Sale).order_by(profit.desc(), Book.id).limit(10),
    }
    for name, column in (("genres", Book.genre), ("stores", Book.purchase_store)):
        result[name] = db.session.query(column, func.count(Book.id), sum0(profit))\
            .join(Sale).group_by(column).order_by(sum0(profit).desc(), column).limit(12)
    return result


def snapshot(names=None):
    """One SQL statement/round trip, including on remote PostgreSQL.

    Aggregate each bounded result into JSON on the database. This also gives
    the dashboard a consistent snapshot while sales are being updated.
    """
    available = queries()
    names = names or list(available)
    sqlite = db.engine.dialect.name == "sqlite"
    row_json = func.json_array if sqlite else func.json_build_array
    aggregate = func.json_group_array if sqlite else func.json_agg
    columns = []
    for name in names:
        sub = available[name].subquery()
        columns.append(select(aggregate(row_json(*sub.c))).select_from(sub).scalar_subquery().label(name))
    row = db.session.execute(select(*columns)).one()
    result = {}
    for name, value in zip(names, row):
        values = json.loads(value) if isinstance(value, str) else value
        result[name] = [json.loads(v) if isinstance(v, str) else v for v in (values or [])]
    return result


def summary(data=None):
    data = data if data is not None else snapshot(["books", "sales", "costs"])
    b, s, costs = data["books"][0], data["sales"][0], data["costs"][0][0]
    profit = s[0] - s[1] - s[2] - b[1] - costs
    return {"purchase": b[0], "sold_purchase": b[1], "inventory_value": b[2],
            "sold_count": b[3], "inventory_count": b[4], "aging_count": b[5],
            "sales": s[0], "fees": s[1], "shipping": s[2], "costs": costs,
            "profit": profit, "cash_flow": s[0] - s[1] - s[2] - b[0] - costs,
            "profit_rate": round(profit / s[0] * 100, 1) if s[0] else 0,
            "sell_through": round(b[3] / (b[3] + b[4]) * 100, 1) if b[3] + b[4] else 0,
            "average_sale": round(s[0] / s[3]) if s[3] else 0}


def monthly(period, data=None):
    data = data if data is not None else snapshot(["monthly_sales", "monthly_purchase", "monthly_costs"])
    rows = {r[0]: r for r in data["monthly_sales"]}
    purchases, costs = dict(data["monthly_purchase"]), dict(data["monthly_costs"])
    now = datetime.now(timezone(timedelta(hours=9))).date()
    last = now.year * 12 + now.month - 1
    keys = [key for key in set(rows) | set(purchases) | set(costs) if key]
    first = last - (5 if period == "6m" else 11)
    if period == "all" and keys:
        y, mo = map(int, min(keys).split("-"))
        first = y * 12 + mo - 1
        y, mo = map(int, max(keys).split("-"))
        last = max(last, y * 12 + mo - 1)
    labels = [f"{i // 12:04d}-{i % 12 + 1:02d}" for i in range(first, last + 1)]
    result = {key: [] for key in ("sales", "profit", "cash_flow", "costs", "purchase")}
    for label in labels:
        r = rows.get(label, (label, 0, 0, 0, 0))
        cost, purchase = costs.get(label, 0), purchases.get(label, 0)
        result["sales"].append(r[1])
        result["profit"].append(r[1] - r[2] - r[3] - r[4] - cost)
        result["cash_flow"].append(r[1] - r[2] - r[3] - purchase - cost)
        result["costs"].append(cost)
        result["purchase"].append(purchase)
    return {"labels": labels, **result}


def breakdown(name, data=None):
    data = data if data is not None else snapshot([name])
    return [{"label": r[0] or "未分類", "count": r[1], "profit": round(r[2])} for r in data[name]]


def rotation(data=None):
    data = data if data is not None else snapshot(["rotation", "median"])
    r = data["rotation"][0]
    return {"average": round(r[0] or 0, 1), "min": round(r[1] or 0), "max": round(r[2] or 0), "count": r[3], "median": round(data["median"][0][0] or 0, 1)}


def ranking(data=None):
    data = data if data is not None else snapshot(["ranking"])
    return [{"title": r[0], "profit": round(r[1]), "rate": round(r[1] / r[2] * 100, 1) if r[2] else None} for r in data["ranking"]]


@analytics_bp.get("/dashboard")
def dashboard():
    period = request.args.get("period", "6m")
    if period not in ("6m", "1y", "all"):
        return jsonify(message="期間を確認してください"), 400
    data = snapshot()
    return jsonify(summary=summary(data), monthly=monthly(period, data), genres=breakdown("genres", data),
                   stores=breakdown("stores", data), rotation=rotation(data), ranking=ranking(data))


# Retain existing API entry points for integrations.
@analytics_bp.get("/summary")
def get_summary():
    return jsonify(summary())


@analytics_bp.get("/monthly")
def get_monthly():
    return jsonify(monthly(request.args.get("period", "6m")))


@analytics_bp.get("/genre-profit")
def get_genres():
    rows = breakdown("genres")
    return jsonify(labels=[r["label"] for r in rows], values=[r["profit"] for r in rows])


@analytics_bp.get("/status")
def get_status():
    counts = db.session.query(sum0(case((Book.sale_id.is_(None), 1), else_=0)),
                              sum0(case((Book.sale_id.isnot(None), 1), else_=0))).one()
    return jsonify(labels=["在庫", "売却済"], values=list(counts))


@analytics_bp.get("/rotation")
def get_rotation():
    return jsonify(rotation())


@analytics_bp.get("/profit-ranking")
def get_ranking():
    return jsonify(ranking())
