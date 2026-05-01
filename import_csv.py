import math
import pandas as pd

from datetime import datetime

from app import create_app

from extensions.db import db

from models.book import Book
from models.sale import Sale
from models.cost import Cost


# =========================
# Flask App
# =========================

app = create_app()

app.app_context().push()


# =========================
# CSV読み込み
# =========================

CSV_PATH = r"C:\Users\Teikyo\Desktop\my-all-directory\application-directory\sedori-stock-app\在庫管理 2ee565fd867b81df92cef7626218f2da_all.csv"

# 全列文字列で読む
# 型崩壊防止
df = pd.read_csv(
    CSV_PATH,
    dtype=str
)


# =========================
# DB初期化
# =========================

print("既存データ削除中...")

Book.query.delete()

Sale.query.delete()

Cost.query.delete()

db.session.commit()

print("削除完了")


# =========================
# Utility
# =========================

def clean_text(value):

    if value is None:
        return None

    # pandas nan 対策
    if isinstance(value, float):

        if math.isnan(value):
            return None

    text = str(value).strip()

    if text.lower() == "nan":
        return None

    if text == "":
        return None

    return text


def clean_number(value):

    value = clean_text(value)

    if value is None:
        return 0

    try:

        return int(float(value))

    except:

        return 0


def parse_date(value):

    value = clean_text(value)

    if not value:
        return None

    try:

        return datetime.strptime(
            value,
            "%Y年%m月%d日"
        )

    except:

        return None


def extract_after_space(value):

    value = clean_text(value)

    if not value:
        return None

    parts = value.split(" ", 1)

    if len(parts) >= 2:
        return parts[1]

    return value


def normalize_status(status):

    status = clean_text(status)

    if status == "在庫あり":
        return "出品中"

    if status == "売却済み":
        return "売却済"

    if status == "進行中":
        return "出品中"

    return status or "出品中"


# =========================
# Import
# =========================

book_count = 0
sale_count = 0
cost_count = 0
skip_count = 0

for _, row in df.iterrows():

    title = clean_text(
        row.get("名前")
    )

    # =========================
    # 空行スキップ
    # =========================

    if not title:

        skip_count += 1

        continue

    # =========================
    # 備品判定
    # =========================

    genre_raw = clean_text(
        row.get("ジャンル")
    )

    genre = extract_after_space(
        genre_raw
    )

    if genre == "備品":

        cost = Cost(

            cost_type="packaging",

            name=title,

            amount=clean_number(
                row.get("仕入れ値")
            ),

            quantity=1,

            memo=clean_text(
                row.get("備考")
            ),

            cost_date=parse_date(
                row.get("仕入れ日")
            )

        )

        db.session.add(cost)

        cost_count += 1

        continue

    # =========================
    # 状態
    # =========================

    status = normalize_status(
        row.get("状態")
    )

    sale = None

    # =========================
    # Sale作成
    # =========================

    if status == "売却済":

        sale = Sale(

            sale_price=clean_number(
                row.get("売上")
            ),

            fee=clean_number(
                row.get("手数料")
            ),

            shipping_cost=clean_number(
                row.get("配送料")
            ),

            sale_date=parse_date(
                row.get("販売日")
            ),

            shipping_method=clean_text(
                row.get("配送手段")
            ),

            status="売却済"

        )

        db.session.add(sale)

        db.session.flush()

        sale_count += 1

    # =========================
    # Book作成
    # =========================

    book = Book(

        title=title,

        isbn=clean_text(
            row.get("ISBN")
        ),

        c_code=clean_text(
            row.get("Cコード")
        ),

        genre=genre,

        publisher=clean_text(
            row.get("出版社")
        ),

        book_format=extract_after_space(
            row.get("形態")
        ),

        target=extract_after_space(
            row.get("販売対象")
        ),

        purchase_price=clean_number(
            row.get("仕入れ値")
        ),

        purchase_store=clean_text(
            row.get("仕入れ店舗")
        ),

        purchase_date=parse_date(
            row.get("仕入れ日")
        ),

        sale_id=sale.id if sale else None,

        status=status,

        mercari_url=clean_text(
            row.get("メルカリURL")
        ),

        memo=clean_text(
            row.get("備考")
        )

    )

    db.session.add(book)

    book_count += 1


# =========================
# Commit
# =========================

db.session.commit()


# =========================
# Result
# =========================

print("=================================")

print(f"Book: {book_count}件")

print(f"Sale: {sale_count}件")

print(f"Cost: {cost_count}件")

print(f"Skip: {skip_count}件")

print("インポート完了")

print("=================================")