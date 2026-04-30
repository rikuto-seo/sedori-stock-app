from datetime import datetime

from extensions.db import db


class Book(db.Model):

    __tablename__ = "books"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =========================
    # 商品情報
    # =========================

    title = db.Column(
        db.String(255),
        nullable=False
    )

    isbn = db.Column(
        db.String(20),
        unique=False,
        nullable=True
    )

    c_code = db.Column(
        db.String(20),
        nullable=True
    )

    genre = db.Column(
        db.String(100),
        nullable=True
    )

    publisher = db.Column(
        db.String(100),
        nullable=True
    )

    book_format = db.Column(
        db.String(50),
        nullable=True
    )

    target = db.Column(
        db.String(50),
        nullable=True
    )

    # =========================
    # 仕入れ情報
    # =========================

    purchase_price = db.Column(
        db.Integer,
        nullable=False
    )

    purchase_store = db.Column(
        db.String(100),
        nullable=True
    )

    purchase_date = db.Column(
        db.Date,
        nullable=False
    )

    # =========================
    # 販売情報
    # =========================

    sale_id = db.Column(
        db.Integer,
        db.ForeignKey("sales.id"),
        nullable=True
    )

    # =========================
    # 状態
    # =========================

    status = db.Column(
        db.String(20),
        default="出品中"
    )

    # =========================
    # その他
    # =========================

    mercari_url = db.Column(
        db.Text,
        nullable=True
    )

    memo = db.Column(
        db.Text,
        nullable=True
    )

    # =========================
    # タイムスタンプ
    # =========================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # =========================
    # 利益計算
    # =========================

    @property
    def profit(self):

        if not self.sale:
            return None

        sale_price = (
            self.sale.sale_price or 0
        )

        fee = (
            self.sale.fee or 0
        )

        shipping = (
            self.sale.shipping_cost or 0
        )

        purchase_price = (
            self.purchase_price or 0
        )

        # =========================
        # セット販売按分
        # =========================

        book_count = len(
            self.sale.books
        )

        if book_count <= 0:
            return None

        allocated_sale = sale_price / book_count

        allocated_fee = fee / book_count

        allocated_shipping = shipping / book_count

        profit = (

            allocated_sale

            -

            allocated_fee

            -

            allocated_shipping

            -

            purchase_price

        )

        return round(profit)

    # =========================
    # JSON化
    # =========================

    def to_dict(self):

        sale_data = None

        if self.sale:

            sale_data = {

                "id":
                    self.sale.id,

                "sale_price":
                    self.sale.sale_price,

                "fee":
                    self.sale.fee,

                "shipping_cost":
                    self.sale.shipping_cost,

                "sale_date":
                    (
                        self.sale.sale_date.isoformat()
                        if self.sale.sale_date
                        else None
                    ),

                "shipping_method":
                    self.sale.shipping_method,

                "status":
                    self.sale.status

            }

        return {

            "id":
                self.id,

            "title":
                self.title,

            "isbn":
                self.isbn,

            "c_code":
                self.c_code,

            "genre":
                self.genre,

            "publisher":
                self.publisher,

            "book_format":
                self.book_format,

            "target":
                self.target,

            "purchase_price":
                self.purchase_price,

            "purchase_store":
                self.purchase_store,

            "purchase_date":
                (
                    self.purchase_date.isoformat()
                    if self.purchase_date
                    else None
                ),

            "sale_id":
                self.sale_id,

            "sale":
                sale_data,

            "status":
                self.status,

            "mercari_url":
                self.mercari_url,

            "memo":
                self.memo,

            "profit":
                self.profit

        }