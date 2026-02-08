# db/schema.py
from __future__ import annotations

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
    Initialize DB schema for bilant.
    Note: Later we can replace this with Alembic migrations.
    """
    db = get_db()
    with db.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    db.commit()
