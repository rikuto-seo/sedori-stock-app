import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from app import create_app
from config import database_settings
from extensions.db import db


class VercelTests(unittest.TestCase):
    def test_postgres_alias_and_bounded_connections(self):
        uri, options, error = database_settings(" postgres://user:password@example.test/books ", True)
        self.assertTrue(uri.startswith("postgresql://"))
        self.assertIsNone(error)
        self.assertEqual(options["connect_args"]["connect_timeout"], 5)
        self.assertTrue(options["pool_pre_ping"])

    def test_invalid_hosted_database_never_uses_a_local_file(self):
        for value in (None, "sqlite:///database.db", "not-a-url",
                      "postgresql://user:password@dpg-example/books"):
            uri, options, error = database_settings(value, True)
            self.assertEqual(uri, "sqlite:///:memory:")
            self.assertTrue(error)
            self.assertNotIn("password", error)

    def test_local_sqlite_remains_supported(self):
        uri, options, error = database_settings(None, False)
        self.assertEqual(uri, "sqlite:///database.db")
        self.assertIsNone(error)

    def test_hosted_startup_never_initializes_schema(self):
        with patch.object(db, "create_all", side_effect=AssertionError("startup DDL")):
            app = create_app({"TESTING": False, "AUTO_CREATE_TABLES": False,
                              "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "DATABASE_CONFIGURATION_ERROR": None})
            self.assertEqual(app.test_client().get("/").status_code, 200)
        with app.app_context():
            db.engine.dispose()

    def test_vercel_import_without_database_or_filesystem_writes(self):
        env = os.environ.copy()
        env["VERCEL"] = "1"
        env.pop("DATABASE_URL", None)
        script = """
from unittest.mock import patch
with patch('sqlalchemy.engine.Engine.connect', side_effect=AssertionError('startup connection')):
    from app import app
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
    client = app.test_client()
    assert client.get('/').status_code == 200
    assert client.get('/health').status_code == 200
    assert client.get('/api/books').status_code == 503
"""
        result = subprocess.run([sys.executable, "-c", script], env=env,
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unreachable_database_does_not_break_page_import(self):
        env = os.environ.copy()
        env.update(VERCEL="1", DATABASE_URL="postgresql://stock:test-password@127.0.0.1:1/stock")
        script = """
from app import app
client = app.test_client()
assert client.get('/').status_code == 200
assert client.get('/health').status_code == 200
response = client.get('/api/books')
assert response.status_code == 503
assert 'test-password' not in response.get_data(as_text=True)
"""
        result = subprocess.run([sys.executable, "-c", script], env=env,
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("test-password", result.stderr)


if __name__ == "__main__":
    unittest.main()
