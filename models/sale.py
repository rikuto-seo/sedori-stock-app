from extensions.db import db


class Sale(db.Model):

    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)

    sale_price = db.Column(db.Integer, default=0)
    fee = db.Column(db.Integer, default=0)
    shipping_cost = db.Column(db.Integer, default=0)

    sale_date = db.Column(db.DateTime)

    shipping_method = db.Column(db.String(100))

    status = db.Column(db.String(50), default="出品中")

    # ★ 追加（超重要）
    book_count = db.Column(db.Integer, default=1)

    books = db.relationship(
        "Book",
        backref="sale",
        lazy="select"   # ← 明示
    )

    def to_dict(self):

        return {

            "id": self.id,

            "sale_price": self.sale_price,

            "fee": self.fee,

            "shipping_cost": self.shipping_cost,

            "sale_date": (
                self.sale_date.strftime(
                    "%Y-%m-%d"
                )
                if self.sale_date
                else None
            ),

            "shipping_method": self.shipping_method,

            "status": self.status,

            "book_ids": [
                b.id
                for b in self.books
            ]

        }