# db/connection.py
from __future__ import annotations

from typing import Optional

import psycopg
from flask import current_app, g
from psycopg.rows import dict_row


def get_db() -> psycopg.Connection:
    """
    Get a PostgreSQL connection for the current request.
    Connection is stored in Flask's g (request scope).
    """
    if "db" not in g:
        dsn = current_app.config.get("DATABASE_URL")
        if not dsn:
            raise RuntimeError("DATABASE_URL is not set")

        g.db = psycopg.connect(
            dsn,
            row_factory=dict_row,
        )

    return g.db  # type: ignore[return-value]


def close_db(e: Optional[BaseException] = None) -> None:
    """
    Close the database connection at the end of the request.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()
