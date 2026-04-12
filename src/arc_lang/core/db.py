from __future__ import annotations
import sqlite3
from arc_lang.core.config import DB_PATH, SQL_INIT_PATH


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    sql = SQL_INIT_PATH.read_text(encoding="utf-8")
    with connect() as conn:
        conn.executescript(sql)
        conn.commit()
