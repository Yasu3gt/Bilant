from flask import Blueprint, render_template, request

from repositories.transactions import (
    list_transactions_for_month,
    summarize_for_month,
)

ledger_bp = Blueprint("ledger", __name__, url_prefix="/ledger")


TYPE_LABEL = {
    "income": "収入",
    "expense": "支出",
}

@ledger_bp.get("")
def ledger():
    ym = request.args.get("month")
    if not ym:
        # 既存の実装に合わせて “当月” を作る（今は最小）
        from datetime import date
        today = date.today()
        ym = f"{today.year:04d}-{today.month:02d}"

    summary = summarize_for_month(ym)
    rows = list_transactions_for_month(ym)

    return render_template(
        "ledger.html",
        ym=ym,
        summary=summary,
        items=rows,
        type_label=TYPE_LABEL,
    )
