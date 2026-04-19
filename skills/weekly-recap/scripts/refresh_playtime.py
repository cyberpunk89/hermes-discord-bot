#!/usr/bin/env python3
import sys
import os
import requests

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
import _load_env  # noqa: F401
os.environ.setdefault("DB_PATH", os.path.join(_PROJECT_DIR, "watchlist.db"))
from database import get_linked_users, upsert_user_games

STEAM_KEY = os.environ.get("STEAM_API_KEY", "")
STEAM_BASE = "https://api.steampowered.com"


def fetch_library(steam_id):
    try:
        r = requests.get(
            f"{STEAM_BASE}/IPlayerService/GetOwnedGames/v1/",
            params={"key": STEAM_KEY, "steamid": steam_id, "include_appinfo": 1, "include_played_free_games": 1},
            timeout=15,
        )
        return r.json().get("response", {}).get("games", [])
    except Exception:
        return []


def main():
    users = get_linked_users()
    if not users:
        print("NO_USERS")
        return
    for user in users:
        games = fetch_library(user["steam_id"])
        if games:
            upsert_user_games(user["discord_id"], [
                {"appid": g["appid"], "name": g.get("name", "Unknown"), "playtime_forever": g.get("playtime_forever", 0)}
                for g in games
            ])
            print(f"REFRESHED: {user['discord_name']} ({len(games)} games)")
        else:
            print(f"SKIPPED: {user['discord_name']} (private or error)")


if __name__ == "__main__":
    main()
