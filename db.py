import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app, g

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  txn_type TEXT NOT NULL CHECK (txn_type IN ('income','expense')),
  category TEXT NOT NULL,
  txn_date TEXT NOT NULL, -- YYYY-MM-DD
  amount INTEGER NOT NULL CHECK (amount >= 0),
  memo TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_txn_date ON transactions(txn_date);
CREATE INDEX IF NOT EXISTS idx_transactions_type_date ON transactions(txn_type, txn_date);
"""


def _db_path() -> str:
    """Return absolute path to the SQLite DB file."""
    # Prefer Flask instance folder (safe for runtime writes)
    db_path = current_app.config.get("DATABASE")
    if db_path:
        return db_path
    instance_path = current_app.instance_path
    os.makedirs(instance_path, exist_ok=True)
    return os.path.join(instance_path, "bilant.db")


def get_db() -> sqlite3.Connection:
    """Get a sqlite3 connection for the current request."""
    if "db" not in g:
        conn = sqlite3.connect(_db_path())
        conn.row_factory = sqlite3.Row
        # Basic hardening / correctness
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db  # type: ignore[return-value]


def close_db(e: Optional[BaseException] = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    db.executescript(SCHEMA_SQL)
    db.commit()


def insert_transaction(
    txn_type: str,
    category: str,
    txn_date: str,
    amount: int,
    memo: str = "",
) -> int:
    db = get_db()
    created_at = datetime.now().isoformat(timespec="seconds")
    cur = db.execute(
        """
        INSERT INTO transactions (txn_type, category, txn_date, amount, memo, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (txn_type, category, txn_date, amount, memo, created_at),
    )
    db.commit()
    return int(cur.lastrowid)


def list_transactions_for_month(ym: str) -> List[sqlite3.Row]:
    """List transactions for a given month (ym='YYYY-MM')."""
    db = get_db()
    start = f"{ym}-01"
    # End boundary: use SQLite date arithmetic to get first day of next month
    rows = db.execute(
        """
        SELECT id, txn_type, category, txn_date, amount, memo, created_at
        FROM transactions
        WHERE txn_date >= ?
          AND txn_date < date(?, '+1 month')
        ORDER BY txn_date DESC, id DESC
        """,
        (start, start),
    ).fetchall()
    return list(rows)


def summarize_for_month(ym: str) -> Dict[str, int]:
    db = get_db()
    start = f"{ym}-01"
    row = db.execute(
        """
        SELECT
          COALESCE(SUM(CASE WHEN txn_type='income' THEN amount END), 0) AS income_total,
          COALESCE(SUM(CASE WHEN txn_type='expense' THEN amount END), 0) AS expense_total
        FROM transactions
        WHERE txn_date >= ?
          AND txn_date < date(?, '+1 month')
        """,
        (start, start),
    ).fetchone()

    income_total = int(row["income_total"]) if row else 0
    expense_total = int(row["expense_total"]) if row else 0
    return {
        "income_total": income_total,
        "expense_total": expense_total,
        "balance": income_total - expense_total,
    }
