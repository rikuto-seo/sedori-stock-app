from datetime import datetime
from extensions.db import db


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)

    # 商品情報
    title = db.Column(db.String(255), nullable=False)
    isbn = db.Column(db.String(20), unique=False, nullable=True)
    c_code = db.Column(db.String(20), nullable=True)
    genre = db.Column(db.String(100), nullable=True)
    publisher = db.Column(db.String(100), nullable=True)
    book_format = db.Column(db.String(50), nullable=True)
    target = db.Column(db.String(50), nullable=True)

    # 仕入れ情報
    purchase_price = db.Column(db.Integer, nullable=False)
    purchase_store = db.Column(db.String(100), nullable=True)
    purchase_date = db.Column(db.Date, nullable=False)

    # 販売情報
    sale_price = db.Column(db.Integer, nullable=True)
    fee = db.Column(db.Integer, nullable=True)
    shipping_cost = db.Column(db.Integer, nullable=True)
    sale_date = db.Column(db.Date, nullable=True)
    shipping_method = db.Column(db.String(50), nullable=True)

    # 状態
    status = db.Column(db.String(20), default="未出品")

    # その他
    mercari_url = db.Column(db.Text, nullable=True)
    memo = db.Column(db.Text, nullable=True)

    # タイムスタンプ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    @property
    def profit(self):
        if self.sale_price is None:
            return None

        fee = self.fee or 0
        shipping = self.shipping_cost or 0

        return self.sale_price - fee - shipping - self.purchase_price

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "isbn": self.isbn,
            "c_code": self.c_code,
            "genre": self.genre,
            "publisher": self.publisher,
            "book_format": self.book_format,
            "target": self.target,
            "purchase_price": self.purchase_price,
            "purchase_store": self.purchase_store,
            "purchase_date": self.purchase_date.isoformat() if self.purchase_date else None,
            "sale_price": self.sale_price,
            "fee": self.fee,
            "shipping_cost": self.shipping_cost,
            "sale_date": self.sale_date.isoformat() if self.sale_date else None,
            "shipping_method": self.shipping_method,
            "status": self.status,
            "mercari_url": self.mercari_url,
            "memo": self.memo,
            "profit": self.profit,
        }