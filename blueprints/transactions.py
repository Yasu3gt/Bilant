from flask import Blueprint, redirect, render_template, request, url_for

from repositories.transactions import insert_transaction

bp = Blueprint("transactions", __name__, url_prefix="/transaction")

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
    ("income", "収入"),
    ("expense", "支出"),
]

@bp.get("/new")
def new():
    form = {}
    errors = {}
    return render_template(
        "transaction_form.html",
        categories=CATEGORIES,
        txn_types=TXN_TYPES,
        form=form,
        errors=errors,
    )

@bp.post("/new")
def create():
    txn_type = request.form.get("txn_type", "")
    category = request.form.get("category", "")
    txn_date = request.form.get("txn_date", "")
    amount = request.form.get("amount", "").strip()
    memo = request.form.get("memo", "")

    # 最小バリデーション（今は壊さない）
    if not (txn_type and category and txn_date and amount.isdigit()):
        # 失敗時はフォーム再表示（必要ならエラーメッセージ追加可）
        return render_template(
            "transaction_form.html",
            categories=CATEGORIES,
            txn_types=TXN_TYPES,
            error="入力内容を確認してください",
        ), 400

    insert_transaction(
        txn_type=txn_type,
        category=category,
        txn_date=txn_date,
        amount=int(amount),
        memo=memo,
    )
    return redirect(url_for("ledger.ledger"))
