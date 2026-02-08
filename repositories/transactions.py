# repositories/transactions.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Tuple

from db.connection import get_db


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
  id BIGSERIAL PRIMARY KEY,
  txn_type TEXT NOT NULL CHECK (txn_type IN ('income','expense')),
  category TEXT NOT NULL,
  txn_date DATE NOT NULL,
  amount INTEGER NOT NULL CHECK (amount >= 0),
  memo TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_txn_date ON transactions(txn_date);
CREATE INDEX IF NOT EXISTS idx_transactions_type_date ON transactions(txn_type, txn_date);
"""


def init_db() -> None:
    """
    Initialize DB schema (temporary place).
    Note: Later we can move this into db/schema.py or migrations.
    """
    db = get_db()
    with db.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    db.commit()


def _month_range(ym: str) -> Tuple[date, date]:
    """
    ym='YYYY-MM' -> (start, end)
    end is the first day of the next month.
    """
    y, m = ym.split("-")
    y_i, m_i = int(y), int(m)
    start = date(y_i, m_i, 1)
    if m_i == 12:
        end = date(y_i + 1, 1, 1)
    else:
        end = date(y_i, m_i + 1, 1)
    return start, end


def insert_transaction(
    txn_type: str,
    category: str,
    txn_date: str,  # 'YYYY-MM-DD'
    amount: int,
    memo: str = "",
) -> int:
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            INSERT INTO transactions (txn_type, category, txn_date, amount, memo)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (txn_type, category, txn_date, amount, memo),
        )
        new_id = cur.fetchone()["id"]
    db.commit()
    return int(new_id)


def list_transactions_for_month(ym: str) -> List[Dict[str, Any]]:
    start, end = _month_range(ym)
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT id, txn_type, category, txn_date, amount, memo, created_at
            FROM transactions
            WHERE txn_date >= %s AND txn_date < %s
            ORDER BY txn_date DESC, id DESC
            """,
            (start, end),
        )
        rows = cur.fetchall()
    return list(rows)


def summarize_for_month(ym: str) -> Dict[str, int]:
    start, end = _month_range(ym)
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
              COALESCE(SUM(CASE WHEN txn_type='income' THEN amount END), 0) AS income_total,
              COALESCE(SUM(CASE WHEN txn_type='expense' THEN amount END), 0) AS expense_total
            FROM transactions
            WHERE txn_date >= %s AND txn_date < %s
            """,
            (start, end),
        )
        row = cur.fetchone()

    income_total = int(row["income_total"])
    expense_total = int(row["expense_total"])
    return {
        "income_total": income_total,
        "expense_total": expense_total,
        "balance": income_total - expense_total,
    }
