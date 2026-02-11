import os
from flask import Flask
from dotenv import load_dotenv

from db.connection import close_db
from db.schema import init_db

from blueprints.home import home_bp
from blueprints.ledger import ledger_bp
from blueprints.transactions import transactions_bp


def create_app() -> Flask:
    # ローカルは .env から環境変数を読み込む（本番は環境側で注入される想定）
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("config.Config")

    os.makedirs(app.instance_path, exist_ok=True)
    app.teardown_appcontext(close_db)

    # Blueprint登録
    app.register_blueprint(home_bp)
    app.register_blueprint(ledger_bp)
    app.register_blueprint(transactions_bp)

    # DB初期化は「起動時」ではなく「必要なときだけ」実行できるようにする
    @app.cli.command("init-db")
    def init_db_command():
        """Initialize the database schema."""
        with app.app_context():
            init_db()
        print("Initialized the database.")

    return app
