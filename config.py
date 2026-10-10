import os

from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

# Vercel supplies environment variables; never load a developer's .env there.
if os.getenv("VERCEL") != "1":
    load_dotenv()


def database_settings(value, hosted=False):
    """Normalize URLs without connecting or writing to the filesystem."""
    value = (value or "").strip()
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://"):]
    error = None
    if not value:
        if hosted:
            error = "Vercelの環境変数DATABASE_URLに、外部接続用PostgreSQL URLを設定してください。"
        return ("sqlite:///:memory:" if hosted else "sqlite:///database.db"), {}, error
    try:
        url = make_url(value)
        backend = url.get_backend_name()
        if backend not in ("postgresql", "sqlite"):
            error = "DATABASE_URLにはPostgreSQLの接続URLを設定してください。"
        elif hosted and backend == "sqlite":
            error = "Vercelでは在庫の永続保存に外部PostgreSQLを使用してください。"
        elif hosted and url.host and url.host.startswith("dpg-") and "." not in url.host:
            error = "RenderのInternal Database URLは使用できません。External Database URLを設定してください。"
        options = {}
        if backend == "postgresql":
            options = {"pool_pre_ping": True, "pool_recycle": 300,
                       "pool_size": 2, "max_overflow": 1, "pool_timeout": 5,
                       "connect_args": {"connect_timeout": 5}}
        if error:
            return "sqlite:///:memory:", {}, error
        return value, options, None
    except (ArgumentError, ValueError):
        return "sqlite:///:memory:", {}, "DATABASE_URLの形式を確認してください。接続URL全体を設定する必要があります。"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    IS_VERCEL = os.getenv("VERCEL") == "1"
    SQLALCHEMY_DATABASE_URI, SQLALCHEMY_ENGINE_OPTIONS, DATABASE_CONFIGURATION_ERROR = database_settings(
        os.getenv("DATABASE_URL"), IS_VERCEL
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Existing production databases are reused. Schema creation is an explicit CLI task.
    AUTO_CREATE_TABLES = not IS_VERCEL and not os.getenv("DATABASE_URL")
