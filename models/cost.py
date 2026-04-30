from datetime import datetime

from extensions.db import db


class Cost(db.Model):

    __tablename__ = "costs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # 種別
    # packaging / coupon
    cost_type = db.Column(
        db.String(50),
        nullable=False
    )

    # 名前
    # OPP袋 / 封筒 / クーポン
    name = db.Column(
        db.String(100),
        nullable=False
    )

    # 金額
    amount = db.Column(
        db.Integer,
        nullable=False
    )

    # 個数
    quantity = db.Column(
        db.Integer,
        nullable=True
    )

    # メモ
    memo = db.Column(
        db.Text,
        nullable=True
    )

    # 日付
    cost_date = db.Column(
        db.Date,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):

        return {

            "id": self.id,
            "cost_type": self.cost_type,
            "name": self.name,
            "amount": self.amount,
            "quantity": self.quantity,
            "memo": self.memo,
            "cost_date":
                self.cost_date.isoformat()

        }