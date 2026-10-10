import unittest
from unittest.mock import patch
from datetime import datetime
from app import create_app
from extensions.db import db
from models.book import Book
from models.sale import Sale
from services import isbn


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
        self.context = self.app.app_context()
        self.context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def book(self, title="本", price=100):
        response = self.client.post("/api/books", json={"title": title, "purchase_price": price, "purchase_date": "2026-10-01"})
        self.assertEqual(response.status_code, 201)
        return response.json["id"]

    def test_pages_and_empty_dashboard(self):
        for path in ("/", "/inventory", "/costs", "/analytics", "/api/analytics/dashboard"):
            self.assertEqual(self.client.get(path).status_code, 200)
        data = self.client.get("/api/analytics/dashboard").json
        self.assertEqual(data["summary"]["profit"], 0)
        self.assertEqual(len(data["monthly"]["labels"]), 6)

    def test_batch_atomic_validation(self):
        good = {"title":"本A", "purchase_price":100}
        response = self.client.post("/api/books/batch",json={"books":[good,{"title":""}]})
        self.assertEqual(response.status_code,400)
        self.assertEqual(Book.query.count(),0)
        response = self.client.post("/api/books/batch",json={"books":[good,good]})
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.json["count"],2)
        self.assertEqual(Book.query.count(),2)

    def test_batch_limit_and_invalid_amounts(self):
        for entries in ([],[{}]*201):
            self.assertEqual(self.client.post("/api/books/batch",json={"books":entries}).status_code,400)
        for amount in (-1,1.5,True,"abc"):
            self.assertEqual(self.client.post("/api/books",json={"title":"本", "purchase_price":amount}).status_code,400)
        self.assertEqual(self.client.post("/api/books",json={"title":"本", "purchase_date":"2026-13-01"}).status_code,400)

    def test_isbn_normalization(self):
        self.assertEqual(isbn.normalize_isbn("4-10-101001-3"),"9784101010014")
        self.assertEqual(isbn.normalize_isbn("９７８４１０１０１００１４"),"9784101010014")
        with self.assertRaises(ValueError): isbn.normalize_isbn("9784101010015")
        self.assertEqual(self.client.get("/scan/isbn/invalid").status_code,400)

    def test_provider_fallback_and_cache(self):
        isbn._cache.clear()
        with patch.object(isbn,"PROVIDERS",(lambda n: None,lambda n:{"title":"本A","source":"mock"})):
            response = self.client.get("/scan/isbn/9784101010014")
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json["source"],"mock")
        with patch.object(isbn,"PROVIDERS",(lambda n: self.fail("cache miss"),)):
            self.assertEqual(self.client.get("/scan/isbn/9784101010014").status_code,200)
        isbn._cache.clear()

    def test_provider_timeout_and_not_found(self):
        import requests
        isbn._cache.clear()
        def fail(n): raise requests.Timeout()
        with patch.object(isbn,"PROVIDERS",(fail,lambda n: None)):
            self.assertEqual(self.client.get("/scan/isbn/9784101010014").status_code,503)
        with patch.object(isbn,"PROVIDERS",(lambda n: None,)):
            self.assertEqual(self.client.get("/scan/isbn/9784101010014").status_code,404)

    def test_sale_edit_does_not_duplicate_sales(self):
        book_id = self.book()
        for price in (500,600):
            self.assertEqual(self.client.patch(f"/api/books/{book_id}/sale",json={"sale_price":price}).status_code,200)
        self.assertEqual(Sale.query.count(),1)
        self.assertEqual(self.client.get("/api/analytics/summary").json["sales"],600)
        self.client.patch(f"/api/books/{book_id}/sale",json={"sale_price":0})
        self.assertEqual(Sale.query.count(),0)
        self.assertEqual(self.client.get("/api/analytics/summary").json["sales"],0)

    def test_group_profit_and_inventory_accounting(self):
        a,b = self.book("本A",100),self.book("本B",200)
        self.book("在庫",300)
        self.client.post("/api/costs",json={"cost_type":"packaging","name":"封筒","amount":50})
        response = self.client.post("/api/sales/group",json={"book_ids":[a,b],"sale_price":1000,"fee":100,"shipping_cost":200,"sale_date":"2026-10-05"})
        self.assertEqual(response.status_code,201)
        data = self.client.get("/api/analytics/dashboard?period=all").json
        s = data["summary"]
        self.assertEqual((s["profit"],s["cash_flow"],s["inventory_value"]),(350,50,300))
        self.assertEqual((s["sales"],s["sold_count"],s["inventory_count"]),(1000,2,1))
        i=data["monthly"]["labels"].index("2026-10")
        self.assertEqual(data["monthly"]["profit"][i],350)
        self.assertEqual(sum(r["profit"] for r in data["ranking"]),400)
        self.assertEqual(data["rotation"]["average"],4)
        self.assertEqual(data["rotation"]["median"],4)
        self.assertEqual(self.client.get("/api/books").json[0]["sale"],None)
        self.assertEqual(self.client.patch(f"/api/books/{a}/sale",json={"sale_price":600}).status_code,409)

    def test_reject_invalid_group_without_writes(self):
        a = self.book()
        for ids in ([a,a],[a,9999],[]):
            self.assertIn(self.client.post("/api/sales/group",json={"book_ids":ids,"sale_price":500}).status_code,(400,409))
        self.assertEqual(Sale.query.count(),0)
        self.client.patch(f"/api/books/{a}/sale",json={"sale_price":500})
        self.assertEqual(self.client.post("/api/sales/group",json={"book_ids":[a],"sale_price":500}).status_code,409)

    def test_dashboard_uses_one_statement(self):
        from sqlalchemy import event
        statements = []
        def record(connection, cursor, statement, parameters, context, many):
            statements.append(statement)
        event.listen(db.engine, "before_cursor_execute", record)
        try:
            self.assertEqual(self.client.get("/api/analytics/dashboard").status_code,200)
        finally:
            event.remove(db.engine, "before_cursor_execute", record)
        self.assertEqual(len(statements),1)

    def test_orphan_sale_not_counted(self):
        db.session.add(Sale(sale_price=900, book_count=1, sale_date=datetime(2026,10,1)))
        db.session.commit()
        self.assertEqual(self.client.get("/api/analytics/summary").json["sales"],0)

    def test_coupon_and_delete_protection(self):
        self.assertEqual(self.client.post("/api/costs",json={"cost_type":"coupon","name":"値引き","amount":100}).status_code,201)
        self.assertEqual(self.client.get("/api/analytics/summary").json["costs"],-100)
        a=self.book()
        self.client.patch(f"/api/books/{a}/sale",json={"sale_price":500})
        self.assertEqual(self.client.delete(f"/api/books/{a}").status_code,409)


if __name__ == "__main__":
    unittest.main()
