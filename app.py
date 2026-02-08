from __future__ import annotations

from datetime import date

from flask import Flask, redirect, render_template, request, url_for

from db import close_db, init_db, insert_transaction, list_transactions_for_month, summarize_for_month
import os

CATEGORIES = [
    "住居費",
    "食費",
    "保険・税金",
    "電気",
    "ガス",
    "水道",
    "交際費",
    "通信費",
    "雑費",
    "その他",
]

TXN_TYPES = [
    ("expense", "支出"),
    ("income", "収入"),
]

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    # SQLite file location (instance folder is writable and safe)
    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, "bilant.db"),
        SECRET_KEY="dev",  # 後で変更（CSRF等を入れる場合）
    )

    # DB lifecycle
    app.teardown_appcontext(close_db)

    @app.before_request
    def _ensure_db() -> None:
        # MVP: リクエスト前に一度だけテーブルがあることを保証
        init_db()

    @app.get("/")
    def index():
        # トップは当月サマリも出しておく
        ym = date.today().strftime("%Y-%m")
        summary = summarize_for_month(ym)
        return render_template("index.html", ym=ym, summary=summary)

    @app.route("/transaction/new", methods=["GET", "POST"])
    def transaction_new():
        if request.method == "GET":
            return render_template(
                "transaction_form.html",
                categories=CATEGORIES,
                txn_types=TXN_TYPES,
                default_date=date.today().isoformat(),
                form={},
                errors={},
            )

        # POST: validate
        txn_type = (request.form.get("txn_type") or "").strip()
        category = (request.form.get("category") or "").strip()
        txn_date = (request.form.get("txn_date") or "").strip()
        amount_raw = (request.form.get("amount") or "").strip()
        memo = (request.form.get("memo") or "").strip()

        errors: dict[str, str] = {}
        if txn_type not in {"income", "expense"}:
            errors["txn_type"] = "収支区分を選択してください。"
        if category not in set(CATEGORIES):
            errors["category"] = "収支項目を選択してください。"
        if not txn_date:
            errors["txn_date"] = "年月日を入力してください。"
        # amount
        try:
            amount = int(amount_raw)
            if amount < 0:
                raise ValueError
        except Exception:
            errors["amount"] = "金額は0以上の整数で入力してください。"
            amount = 0

        form = {
            "txn_type": txn_type,
            "category": category,
            "txn_date": txn_date,
            "amount": amount_raw,
            "memo": memo,
        }

        if errors:
            return render_template(
                "transaction_form.html",
                categories=CATEGORIES,
                txn_types=TXN_TYPES,
                default_date=date.today().isoformat(),
                form=form,
                errors=errors,
            ), 400

        insert_transaction(txn_type=txn_type, category=category, txn_date=txn_date, amount=amount, memo=memo)
        ym = txn_date[:7] if len(txn_date) >= 7 else date.today().strftime("%Y-%m")
        return redirect(url_for("ledger", month=ym))

    @app.get("/ledger")
    def ledger():
        ym = (request.args.get("month") or "").strip()
        if not ym:
            ym = date.today().strftime("%Y-%m")

        items = list_transactions_for_month(ym)
        summary = summarize_for_month(ym)

        # 表示用ラベル
        type_label = {"income": "収入", "expense": "支出"}

        return render_template(
            "ledger.html",
            ym=ym,
            items=items,
            summary=summary,
            type_label=type_label,
        )

    return app


app = create_app()

app.config.from_mapping(
    DATABASE_URL = os.environ.get("DATABASE_URL"),
    SECRET_KEY = "dev"
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
