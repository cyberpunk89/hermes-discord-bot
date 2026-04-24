"""
Unified cache layer for all external API responses.
Stores cached data in SQLite with TTL expiration.
"""
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Optional

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "watchlist.db"))


def _get_db() -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_cache_table():
    """Create cache table if it doesn't exist."""
    with _get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                cache_value TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_expires ON api_cache(expires_at)
        """)


def _is_expired(expires_at: str) -> bool:
    """Check if cache entry is expired."""
    try:
        expiry = datetime.fromisoformat(expires_at)
        return datetime.now() > expiry
    except Exception:
        return True


def get_cache(cache_key: str, ttl_seconds: int = 3600) -> Optional[Any]:
    """
    Get cached value if not expired.
    
    Args:
        cache_key: Unique identifier for cache entry
        ttl_seconds: Time-to-live in seconds (default 1 hour)
    
    Returns:
        Cached value deserialized from JSON, or None if not found/expired
    """
    init_cache_table()
    try:
        conn = _get_db()
        row = conn.execute(
            "SELECT cache_value, expires_at FROM api_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        conn.close()

        if not row:
            return None

        if _is_expired(row["expires_at"]):
            # Clean up expired entry
            with _get_db() as conn:
                conn.execute("DELETE FROM api_cache WHERE cache_key = ?", (cache_key,))
            return None

        return json.loads(row["cache_value"])
    except Exception:
        return None


def set_cache(cache_key: str, value: Any, ttl_seconds: int = 3600) -> bool:
    """
    Store value in cache with expiration.
    
    Args:
        cache_key: Unique identifier for cache entry
        value: Value to cache (must be JSON serializable)
        ttl_seconds: Time-to-live in seconds (default 1 hour)
    
    Returns:
        True if successfully cached
    """
    init_cache_table()
    try:
        expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
        cache_value = json.dumps(value)

        with _get_db() as conn:
            conn.execute(
                """INSERT INTO api_cache (cache_key, cache_value, expires_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(cache_key) DO UPDATE SET
                   cache_value=excluded.cache_value,
                   expires_at=excluded.expires_at""",
                (cache_key, cache_value, expires_at),
            )
        return True
    except Exception:
        return False


def delete_cache(cache_key: str) -> bool:
    """Delete a specific cache entry."""
    try:
        with _get_db() as conn:
            cursor = conn.execute("DELETE FROM api_cache WHERE cache_key = ?", (cache_key,))
            return cursor.rowcount > 0
    except Exception:
        return False


def clear_expired_cache():
    """Remove all expired cache entries. Call periodically for maintenance."""
    try:
        with _get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM api_cache WHERE expires_at < ?",
                (datetime.now().isoformat(),),
            )
            return cursor.rowcount
    except Exception:
        return 0
