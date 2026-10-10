import click
from flask import Flask, jsonify, request
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from extensions.db import db

from routes.main import main_bp
from routes.api import api_bp

from config import Config
from routes.scan import scan_bp
from routes.analytics import analytics_bp


def create_app(test_config=None):

    app = Flask(__name__)

    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)
        if "SQLALCHEMY_DATABASE_URI" in test_config and "SQLALCHEMY_ENGINE_OPTIONS" not in test_config:
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

    db.init_app(app)

    # Blueprint登録
    app.register_blueprint(main_bp)

    app.register_blueprint(
        api_bp,
        url_prefix="/api"
    )

    app.register_blueprint(scan_bp, url_prefix="/scan")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    @app.before_request
    def check_database_configuration():
        error = app.config.get("DATABASE_CONFIGURATION_ERROR")
        if error and (request.path.startswith("/api/") or request.path == "/health/ready"):
            return jsonify(message=error), 503

    @app.errorhandler(DBAPIError)
    def database_unavailable(error):
        db.session.rollback()
        # Do not log connection strings, query parameters, or credentials.
        app.logger.error("Database request failed (%s)", type(error).__name__)
        return jsonify(message="DBへ接続できません。DATABASE_URL・外部接続設定・DBの稼働状態を確認してください。"), 503

    @app.get("/health")
    def health():
        return jsonify(status="ok", database_configured=not bool(app.config.get("DATABASE_CONFIGURATION_ERROR")))

    @app.get("/health/ready")
    def ready():
        db.session.execute(text("SELECT 1"))
        return jsonify(status="ok")

    @app.cli.command("init-db")
    def init_db():
        """Create missing tables explicitly, rather than during function startup."""
        if app.config.get("DATABASE_CONFIGURATION_ERROR"):
            raise click.ClickException(app.config["DATABASE_CONFIGURATION_ERROR"])
        db.create_all()
        click.echo("Database tables are ready.")

    if app.testing or app.config.get("AUTO_CREATE_TABLES"):
        with app.app_context():
            db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
