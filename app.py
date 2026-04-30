from flask import Flask

from extensions.db import db

from routes.main import main_bp
from routes.api import api_bp

from config import Config


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    # Blueprint登録
    app.register_blueprint(main_bp)

    app.register_blueprint(
        api_bp,
        url_prefix="/api"
    )

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)