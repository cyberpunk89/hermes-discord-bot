import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "watchlist.db"))


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
        # Existing watchlist tables
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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id)")

        # Steam library tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                discord_id TEXT PRIMARY KEY,
                discord_name TEXT,
                steam_id TEXT,
                linked_at TIMESTAMP,
                opted_in BOOLEAN DEFAULT TRUE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_games (
                discord_id TEXT,
                app_id INTEGER,
                game_name TEXT,
                playtime_minutes INTEGER,
                last_updated TIMESTAMP,
                PRIMARY KEY (discord_id, app_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_news (
                app_id INTEGER,
                gid TEXT PRIMARY KEY,
                title TEXT,
                posted_at TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS playtime_snapshots (
                discord_id TEXT,
                app_id INTEGER,
                game_name TEXT,
                playtime_minutes INTEGER,
                snapshot_date TEXT,
                PRIMARY KEY (discord_id, app_id, snapshot_date)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS game_coop_cache (
                app_id INTEGER PRIMARY KEY,
                is_coop INTEGER NOT NULL,
                coop_modes TEXT,
                fetched_at TEXT NOT NULL
            )
        """)


# ── Watchlist functions (unchanged from original) ────────────────────────────

def add_to_watchlist(user_id, user_name, appid, game_title, target_price=None, notify_any_drop=True, notify_hist_low=True):
    try:
        with get_db_context() as conn:
            conn.execute(
                """INSERT INTO watchlist
                (user_id, user_name, appid, game_title, added_date,
                 target_price, notify_any_drop, notify_hist_low, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, user_name, appid, game_title, datetime.now().isoformat(),
                 target_price, 1 if notify_any_drop else 0, 1 if notify_hist_low else 0, datetime.now().isoformat()),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def remove_from_watchlist(user_id, appid):
    with get_db_context() as conn:
        cursor = conn.execute("DELETE FROM watchlist WHERE user_id = ? AND appid = ?", (user_id, appid))
        return cursor.rowcount > 0


def get_user_watchlist(user_id):
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM watchlist WHERE user_id = ? ORDER BY added_date DESC", (user_id,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_all_watchlist():
    conn = get_db()
    try:
        return [dict(row) for row in conn.execute("SELECT * FROM watchlist").fetchall()]
    finally:
        conn.close()


def update_last_prices(appid, retail_price, keyshop_price):
    with get_db_context() as conn:
        conn.execute(
            "UPDATE watchlist SET last_retail_price = ?, last_keyshop_price = ? WHERE appid = ?",
            (retail_price, keyshop_price, appid),
        )


def set_target_price(user_id, appid, target_price):
    with get_db_context() as conn:
        conn.execute("UPDATE watchlist SET target_price = ? WHERE user_id = ? AND appid = ?", (target_price, user_id, appid))


def toggle_notification(user_id, appid, notification_type, enabled):
    column = "notify_any_drop" if notification_type == "any_drop" else "notify_hist_low"
    with get_db_context() as conn:
        cursor = conn.execute(f"UPDATE watchlist SET {column} = ? WHERE user_id = ? AND appid = ?", (1 if enabled else 0, user_id, appid))
        return cursor.rowcount > 0


def count_user_watchlist(user_id):
    conn = get_db()
    try:
        return conn.execute("SELECT COUNT(*) as count FROM watchlist WHERE user_id = ?", (user_id,)).fetchone()["count"]
    finally:
        conn.close()


def clear_user_watchlist(user_id):
    with get_db_context() as conn:
        return conn.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,)).rowcount


def find_by_game_title(user_id, game_title):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM watchlist WHERE user_id = ? AND LOWER(game_title) LIKE ?",
            (user_id, f"%{game_title.lower()}%"),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── Steam user functions ──────────────────────────────────────────────────────

def link_steam_user(discord_id, discord_name, steam_id):
    with get_db_context() as conn:
        conn.execute(
            """INSERT INTO users (discord_id, discord_name, steam_id, linked_at, opted_in)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(discord_id) DO UPDATE SET steam_id=excluded.steam_id, linked_at=excluded.linked_at""",
            (discord_id, discord_name, steam_id, datetime.now().isoformat()),
        )


def unlink_steam_user(discord_id):
    with get_db_context() as conn:
        conn.execute("DELETE FROM user_games WHERE discord_id = ?", (discord_id,))
        conn.execute("DELETE FROM users WHERE discord_id = ?", (discord_id,))


def get_linked_users():
    conn = get_db()
    try:
        return [dict(row) for row in conn.execute("SELECT * FROM users WHERE opted_in = 1").fetchall()]
    finally:
        conn.close()


def upsert_user_games(discord_id, games):
    with get_db_context() as conn:
        conn.execute("DELETE FROM user_games WHERE discord_id = ?", (discord_id,))
        now = datetime.now().isoformat()
        conn.executemany(
            "INSERT INTO user_games (discord_id, app_id, game_name, playtime_minutes, last_updated) VALUES (?, ?, ?, ?, ?)",
            [(discord_id, g["appid"], g["name"], g["playtime_forever"], now) for g in games],
        )


def get_user_games(discord_id):
    conn = get_db()
    try:
        return [dict(row) for row in conn.execute("SELECT * FROM user_games WHERE discord_id = ?", (discord_id,)).fetchall()]
    finally:
        conn.close()


def get_common_games():
    conn = get_db()
    try:
        users = [row["discord_id"] for row in conn.execute("SELECT discord_id FROM users WHERE opted_in = 1").fetchall()]
        if len(users) < 2:
            return []
        placeholders = ",".join("?" * len(users))
        rows = conn.execute(
            f"""SELECT app_id, game_name, SUM(playtime_minutes) as total_playtime, COUNT(*) as owner_count
            FROM user_games WHERE discord_id IN ({placeholders})
            GROUP BY app_id HAVING owner_count = ?
            ORDER BY total_playtime DESC""",
            users + [len(users)],
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ── Co-op cache functions ─────────────────────────────────────────────────────

def get_coop_cache(app_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT is_coop, coop_modes, fetched_at FROM game_coop_cache WHERE app_id = ?", (app_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def set_coop_cache(app_id, is_coop, coop_modes):
    with get_db_context() as conn:
        conn.execute(
            """INSERT INTO game_coop_cache (app_id, is_coop, coop_modes, fetched_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(app_id) DO UPDATE SET is_coop=excluded.is_coop,
            coop_modes=excluded.coop_modes, fetched_at=excluded.fetched_at""",
            (app_id, 1 if is_coop else 0, coop_modes, datetime.now().isoformat()),
        )


# ── News dedup functions ──────────────────────────────────────────────────────

def is_news_seen(gid):
    conn = get_db()
    try:
        return conn.execute("SELECT 1 FROM seen_news WHERE gid = ?", (gid,)).fetchone() is not None
    finally:
        conn.close()


def add_seen_news(app_id, gid, title):
    try:
        with get_db_context() as conn:
            conn.execute(
                "INSERT INTO seen_news (app_id, gid, title, posted_at) VALUES (?, ?, ?, ?)",
                (app_id, gid, title, datetime.now().isoformat()),
            )
    except sqlite3.IntegrityError:
        pass


# ── Playtime snapshot functions ───────────────────────────────────────────────

def save_playtime_snapshot():
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db_context() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO playtime_snapshots (discord_id, app_id, game_name, playtime_minutes, snapshot_date)
            SELECT discord_id, app_id, game_name, playtime_minutes, ? FROM user_games""",
            (today,),
        )


def get_playtime_since_last_snapshot():
    conn = get_db()
    try:
        last_date = conn.execute(
            "SELECT MAX(snapshot_date) as d FROM playtime_snapshots"
        ).fetchone()["d"]
        if not last_date:
            return []
        rows = conn.execute(
            """SELECT u.discord_id, u.discord_name, ug.app_id, ug.game_name,
                ug.playtime_minutes - COALESCE(ps.playtime_minutes, 0) as delta_minutes
            FROM user_games ug
            JOIN users u ON u.discord_id = ug.discord_id
            LEFT JOIN playtime_snapshots ps ON ps.discord_id = ug.discord_id
                AND ps.app_id = ug.app_id AND ps.snapshot_date = ?
            WHERE ug.playtime_minutes > COALESCE(ps.playtime_minutes, 0)
            ORDER BY delta_minutes DESC""",
            (last_date,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


init_db()
