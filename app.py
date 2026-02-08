import os
from flask import Flask

from db.connection import close_db
from db.schema import init_db

from blueprints.home import bp as home_bp
from blueprints.ledger import bp as ledger_bp
from blueprints.transactions import bp as transactions_bp


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        DATABASE_URL=os.environ.get("DATABASE_URL"),
        SECRET_KEY="dev",
    )

    os.makedirs(app.instance_path, exist_ok=True)

    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    # Blueprint登録
    app.register_blueprint(home_bp)
    app.register_blueprint(ledger_bp)
    app.register_blueprint(transactions_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
