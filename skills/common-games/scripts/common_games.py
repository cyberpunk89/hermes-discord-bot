#!/usr/bin/env python3
import sys
import os
import time
import requests
from datetime import datetime, timedelta

# Import centralized utilities
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _PROJECT_DIR)
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))

import _importer  # noqa: F401
import _load_env  # noqa: F401
from _rate_limiter import STEAM_LIMITER
from database import get_common_games, get_linked_users, get_coop_cache, set_coop_cache
from discord_utils import ensure_display_name
from cache import get_cache, set_cache

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
CACHE_TTL_SECONDS = CACHE_TTL_DAYS * 24 * 3600


def is_cache_fresh(fetched_at):
    try:
        age = datetime.now() - datetime.fromisoformat(fetched_at)
        return age.days < CACHE_TTL_DAYS
    except Exception:
        return False


def fetch_coop_status(app_id):
    # Check new cache layer first
    cache_key = f"coop_{app_id}"
    cached = get_cache(cache_key, ttl_seconds=CACHE_TTL_SECONDS)
    if cached:
        return cached.get("is_coop", False), cached.get("coop_modes", "")

    # Fallback to old DB cache
    db_cached = get_coop_cache(app_id)
    if db_cached and is_cache_fresh(db_cached["fetched_at"]):
        return db_cached["is_coop"], db_cached.get("coop_modes", "")

    try:
        # Rate limit before API call
        STEAM_LIMITER.wait()
        
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

        # Store in both caches
        set_cache(cache_key, {"is_coop": is_coop, "coop_modes": coop_modes}, ttl_seconds=CACHE_TTL_SECONDS)
        set_coop_cache(app_id, is_coop, coop_modes)
        time.sleep(0.3)  # be polite to Steam's API
        return is_coop, coop_modes
    except Exception:
        return False, ""


# Display settings
DEFAULT_GAMES_PER_SECTION = 5
EMOJI_COOP = "🎮"
EMOJI_UNPLAYED = "💎"
EMOJI_NONCOOP = "⚔️"


def format_game_entry(g, section_type):
    """Format a game entry with emoji and multi-line structure."""
    emoji = EMOJI_COOP
    if section_type == "unplayed":
        emoji = EMOJI_UNPLAYED
    elif section_type == "non_coop":
        emoji = EMOJI_NONCOOP
    
    modes = g.get("coop_modes", "Solo adventure")
    if not modes:
        modes = "Solo adventure"
    
    lines = [
        f"{emoji} {g['name']}",
        f"   ⏱ {g['playtime_hours']}h total | {g['owners']} owners",
        f"   Modes: {modes}",
    ]
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Show common games")
    parser.add_argument("--all", action="store_true", help="Show all games (default shows 5 per section)")
    parser.add_argument("--section", type=str, help="Show specific section: coops, unplayed, other")
    args = parser.parse_args()
    
    show_all = args.all
    section_filter = args.section
    
    users = get_linked_users()
    user_count = len(users)
    print(f"LINKED_USERS: {user_count}")

    if user_count == 1:
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
            "app_id": g["app_id"],
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

    limit = 60 if show_all else DEFAULT_GAMES_PER_SECTION
    
    def print_section(title, games_list, section_key):
        if section_filter and section_filter != section_key:
            return
        
        emoji = "📚"
        if section_key == "unplayed":
            emoji = EMOJI_UNPLAYED
        elif section_key == "coops":
            emoji = EMOJI_COOP
        elif section_key == "other":
            emoji = EMOJI_NONCOOP
        
        shown = games_list[:limit]
        if not shown:
            return
            
        print(f"\n{'=' * 40}")
        emoji = "📚" if section_key == "coops" else EMOJI_COOP if section_key == "unplayed" else EMOJI_NONCOOP
        if section_key == "coops":
            print(f"{EMOJI_COOP} CO-OP LIBRARY ({len(shown)} games)")
        elif section_key == "unplayed":
            print(f"{EMOJI_UNPLAYED} UNPLAYED GEMS ({len(shown)} games)")
        elif section_key == "other":
            print(f"{EMOJI_NONCOOP} OTHER COMMON ({len(shown)} games)")
        else:
            print(f"{emoji} {title} ({len(shown)} games)")
        print(f"{'=' * 40}")
        
        for g in shown:
            print(format_game_entry(g, section_key))
            print()
        
        remaining = len(games_list) - limit
        if remaining > 0 and not show_all:
            print(f"📋 ... and {remaining} more. Use --all to see all.")

    print_section("UNPLAYED GEMS", unplayed_gems, "unplayed")
    print_section("CO-OP LIBRARY", coop_played, "coops")
    print_section("OTHER COMMON", non_coop, "other")


if __name__ == "__main__":
    main()
