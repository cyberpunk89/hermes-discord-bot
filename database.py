import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "watchlist.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db_context():
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db_context() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_name TEXT,
                appid TEXT NOT NULL,
                game_title TEXT,
                added_date TEXT NOT NULL,
                target_price REAL,
                notify_any_drop INTEGER DEFAULT 1,
                notify_hist_low INTEGER DEFAULT 1,
                last_retail_price REAL,
                last_keyshop_price REAL,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, appid)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                appid TEXT PRIMARY KEY,
                retail_price REAL,
                keyshop_price REAL,
                historical_retail REAL,
                historical_keyshop REAL,
                last_checked TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_watchlist_user 
            ON watchlist(user_id)
        """)


def add_to_watchlist(
    user_id: str,
    user_name: str,
    appid: str,
    game_title: str,
    target_price: float | None = None,
    notify_any_drop: bool = True,
    notify_hist_low: bool = True,
) -> bool:
    try:
        with get_db_context() as conn:
            conn.execute(
                """INSERT INTO watchlist 
                (user_id, user_name, appid, game_title, added_date, 
                 target_price, notify_any_drop, notify_hist_low, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    user_name,
                    appid,
                    game_title,
                    datetime.now().isoformat(),
                    target_price,
                    1 if notify_any_drop else 0,
                    1 if notify_hist_low else 0,
                    datetime.now().isoformat(),
                ),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def remove_from_watchlist(user_id: str, appid: str) -> bool:
    with get_db_context() as conn:
        cursor = conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND appid = ?",
            (user_id, appid),
        )
        return cursor.rowcount > 0


def get_user_watchlist(user_id: str) -> list[dict]:
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM watchlist WHERE user_id = ? ORDER BY added_date DESC",
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_all_watchlist() -> list[dict]:
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM watchlist").fetchall()
        return [dict(row) for row in rows]


def update_last_prices(
    appid: str, retail_price: float | None, keyshop_price: float | None
):
    with get_db_context() as conn:
        conn.execute(
            "UPDATE watchlist SET last_retail_price = ?, last_keyshop_price = ? WHERE appid = ?",
            (retail_price, keyshop_price, appid),
        )


def set_target_price(user_id: str, appid: str, target_price: float | None):
    with get_db_context() as conn:
        conn.execute(
            "UPDATE watchlist SET target_price = ? WHERE user_id = ? AND appid = ?",
            (target_price, user_id, appid),
        )


def toggle_notification(
    user_id: str, appid: str, notification_type: str, enabled: bool
) -> bool:
    column = (
        "notify_any_drop" if notification_type == "any_drop" else "notify_hist_low"
    )
    with get_db_context() as conn:
        cursor = conn.execute(
            f"UPDATE watchlist SET {column} = ? WHERE user_id = ? AND appid = ?",
            (1 if enabled else 0, user_id, appid),
        )
        return cursor.rowcount > 0


def count_user_watchlist(user_id: str) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM watchlist WHERE user_id = ?", (user_id,)
        )
        return cursor.fetchone()["count"]


def clear_user_watchlist(user_id: str) -> int:
    with get_db_context() as conn:
        cursor = conn.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))
        return cursor.rowcount


def find_by_game_title(user_id: str, game_title: str) -> dict | None:
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM watchlist WHERE user_id = ? AND LOWER(game_title) LIKE ?",
            (user_id, f"%{game_title.lower()}%"),
        ).fetchone()
        return dict(row) if row else None


init_db()