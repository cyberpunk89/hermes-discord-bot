#!/usr/bin/env python3
import sys
import os
import sqlite3

# Import centralized utilities
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _PROJECT_DIR)
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))

import _importer  # noqa: F401
import _load_env  # noqa: F401
from _steam_utils import fetch_library
from _rate_limiter import STEAM_LIMITER
from database import get_linked_users, upsert_user_games
from discord_utils import ensure_display_name

DB_PATH = os.environ.get("DB_PATH", os.path.join(_PROJECT_DIR, "watchlist.db"))


def cleanup_watchlist(discord_id, owned_appids):
    """Remove games from watchlist that user already owns."""
    if not owned_appids:
        return 0
    
    removed_count = 0
    with sqlite3.connect(DB_PATH) as conn:
        # Get watchlist entries for this user
        watchlist = conn.execute(
            "SELECT appid, game_title FROM watchlist WHERE user_id = ?",
            (discord_id,),
        ).fetchall()
        
        for appid, title in watchlist:
            if str(appid) in owned_appids or appid in owned_appids:
                conn.execute(
                    "DELETE FROM watchlist WHERE user_id = ? AND appid = ?",
                    (discord_id, appid),
                )
                removed_count += 1
    
    return removed_count


def main():
    users = get_linked_users()
    if not users:
        print("NO_USERS")
        return
    
    total_removed = 0
    
    for user in users:
        name = ensure_display_name(user)
        
        # Rate limit before API call
        STEAM_LIMITER.wait()
        
        games = fetch_library(user["steam_id"])
        if games:
            # Update library
            owned_appids = {str(g["appid"]) for g in games}
            upsert_user_games(user["discord_id"], [
                {"appid": g["appid"], "name": g.get("name", "Unknown"), "playtime_forever": g.get("playtime_forever", 0)}
                for g in games
            ])
            print(f"REFRESHED: {name} ({len(games)} games)")
            
            # Clean up watchlist for this user
            removed = cleanup_watchlist(user["discord_id"], owned_appids)
            if removed > 0:
                print(f"CLEANED: {removed} game(s) removed from watchlist (already owned)")
                total_removed += removed
        else:
            print(f"SKIPPED: {name} (private or error)")
    
    if total_removed > 0:
        print(f"TOTAL_CLEANED: {total_removed} watchlist entries removed across all users")


if __name__ == "__main__":
    main()
