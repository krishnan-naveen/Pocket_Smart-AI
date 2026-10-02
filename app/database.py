"""Tiny SQLite data layer (users + recommendation history). Uses only the standard library."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator, Optional

from .config import get_settings


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(get_settings().database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE NOT NULL,
                   email TEXT NOT NULL,
                   password_hash TEXT NOT NULL,
                   created_at TEXT NOT NULL)"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS history (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER NOT NULL,
                   category TEXT NOT NULL,
                   budget REAL NOT NULL,
                   request_json TEXT NOT NULL,
                   result_json TEXT NOT NULL,
                   source TEXT NOT NULL,
                   created_at TEXT NOT NULL,
                   FOREIGN KEY (user_id) REFERENCES users(id))"""
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_user(username: str, email: str, password_hash: str) -> Optional[int]:
    """Returns the new user id, or None if the username already exists."""
    try:
        with get_conn() as c:
            cur = c.execute(
                "INSERT INTO users (username, email, password_hash, created_at) VALUES (?,?,?,?)",
                (username, email, password_hash, _now()),
            )
            return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def get_user_by_username(username: str) -> Optional[dict[str, Any]]:
    with get_conn() as c:
        row = c.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[dict[str, Any]]:
    with get_conn() as c:
        row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def save_history(user_id: int, category: str, budget: float, request: dict, result: dict, source: str) -> int:
    with get_conn() as c:
        cur = c.execute(
            "INSERT INTO history (user_id, category, budget, request_json, result_json, source, created_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (user_id, category, budget, json.dumps(request), json.dumps(result), source, _now()),
        )
        return cur.lastrowid


def _history_row(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["request"] = json.loads(d.pop("request_json"))
    d["result"] = json.loads(d.pop("result_json"))
    return d


def list_history(user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    with get_conn() as c:
        rows = c.execute(
            "SELECT * FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
        ).fetchall()
        return [_history_row(r) for r in rows]


def get_history_item(user_id: int, item_id: int) -> Optional[dict[str, Any]]:
    with get_conn() as c:
        row = c.execute(
            "SELECT * FROM history WHERE user_id = ? AND id = ?", (user_id, item_id)
        ).fetchone()
        return _history_row(row) if row else None
