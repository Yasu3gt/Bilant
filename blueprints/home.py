from datetime import date

from flask import Blueprint, render_template

from repositories.transactions import summarize_for_month, list_transactions_for_month

home_bp = Blueprint("home", __name__)

@home_bp.get("/")
def index():
    today = date.today()
    ym = f"{today.year:04d}-{today.month:02d}"
    summary = summarize_for_month(ym)
    rows = list_transactions_for_month(ym)

    return render_template(
        "index.html",
        ym=ym,
        summary=summary,
        rows=rows,
        transactions=rows,
    )
