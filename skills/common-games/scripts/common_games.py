#!/usr/bin/env python3
import sys
import os
import time
import requests

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
import _load_env  # noqa: F401
os.environ.setdefault("DB_PATH", os.path.join(_PROJECT_DIR, "watchlist.db"))
from database import get_common_games, get_linked_users, get_coop_cache, set_coop_cache

STEAM_DETAIL_URL = "https://store.steampowered.com/api/appdetails"

# Steam category IDs that mean you can play together
COOP_CATEGORY_IDS = {
    1,   # Multi-player
    9,   # Co-op
    38,  # Online Co-op
    48,  # LAN Co-op
    49,  # Shared/Split Screen Co-op
    27,  # Cross-Platform Multiplayer
}

COOP_CATEGORY_NAMES = {
    1: "Online Multiplayer",
    9: "Co-op",
    38: "Online Co-op",
    48: "LAN Co-op",
    49: "Split Screen Co-op",
    27: "Cross-Platform Multiplayer",
}

CACHE_TTL_DAYS = 14


def is_cache_fresh(fetched_at):
    from datetime import datetime, timedelta
    try:
        age = datetime.now() - datetime.fromisoformat(fetched_at)
        return age.days < CACHE_TTL_DAYS
    except Exception:
        return False


def fetch_coop_status(app_id):
    cached = get_coop_cache(app_id)
    if cached and is_cache_fresh(cached["fetched_at"]):
        return cached["is_coop"], cached.get("coop_modes", "")

    try:
        r = requests.get(
            STEAM_DETAIL_URL,
            params={"appids": app_id, "filters": "categories", "cc": "us", "l": "en"},
            timeout=8,
        )
        data = r.json().get(str(app_id), {})
        if not data.get("success"):
            return False, ""

        categories = data.get("data", {}).get("categories", [])
        matched = [COOP_CATEGORY_NAMES[c["id"]] for c in categories if c["id"] in COOP_CATEGORY_IDS]
        is_coop = bool(matched)
        coop_modes = ", ".join(matched)
        set_coop_cache(app_id, is_coop, coop_modes)
        time.sleep(0.3)  # be polite to Steam's API
        return is_coop, coop_modes
    except Exception:
        return False, ""


def main():
    users = get_linked_users()
    print(f"LINKED_USERS: {len(users)}")

    if len(users) == 1:
        print("NOT_ENOUGH_USERS")
        return

    games = get_common_games()
    print(f"COMMON_COUNT: {len(games)}")

    if not games:
        return

    unplayed_gems = []
    coop_played = []
    non_coop = []

    for g in games[:60]:
        is_coop, coop_modes = fetch_coop_status(g["app_id"])
        entry = {
            "name": g["game_name"],
            "playtime_hours": g["total_playtime"] // 60,
            "owners": g["owner_count"],
            "coop_modes": coop_modes,
        }

        if is_coop:
            if g["total_playtime"] == 0:
                unplayed_gems.append(entry)
            else:
                coop_played.append(entry)
        else:
            non_coop.append(entry)

    print(f"UNPLAYED_GEMS: {len(unplayed_gems)}")
    print(f"COOP_PLAYED: {len(coop_played)}")
    print(f"NON_COOP: {len(non_coop)}")

    if unplayed_gems:
        print()
        print("SECTION: UNPLAYED_GEMS")
        for g in unplayed_gems:
            print(f"GAME: {g['name']} | OWNERS: {g['owners']} | MODE: {g['coop_modes']}")

    if coop_played:
        print()
        print("SECTION: COOP_LIBRARY")
        for g in coop_played:
            print(f"GAME: {g['name']} | PLAYTIME: {g['playtime_hours']}h | OWNERS: {g['owners']} | MODE: {g['coop_modes']}")

    if non_coop:
        print()
        print("SECTION: OTHER_COMMON")
        for g in non_coop[:10]:
            print(f"GAME: {g['name']} | PLAYTIME: {g['playtime_hours']}h | OWNERS: {g['owners']}")


if __name__ == "__main__":
    main()
