#!/usr/bin/env python3
import sys
import os

# Import centralized utilities
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _PROJECT_DIR)
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))

import _importer  # noqa: F401
import _load_env  # noqa: F401
from _steam_utils import search_steam, fetch_steam_details
from _price_utils import fetch_price_fallback
from _rate_limiter import GG_DEALS_LIMITER, ITAD_LIMITER
from database import get_linked_users, get_user_games
from common_games import fetch_coop_status
from discord_utils import get_display_name, ensure_display_name


def fetch_price(appid):
    """Fetch price with rate limiting and GG.deals primary + ITAD fallback."""
    GG_DEALS_LIMITER.wait()
    return fetch_price_fallback(appid, gg_region="eu", itad_country="DE")


def resolve_members(requested_names, all_users):
    """Match requested names (case-insensitive) against linked users. Returns all if none requested."""
    if not requested_names:
        return all_users
    matched = []
    for name in requested_names:
        name_lower = name.lower()
        for u in all_users:
            if u["discord_name"].lower() == name_lower:
                matched.append(u)
                break
    return matched


def user_owns_game(discord_id, appid):
    games = get_user_games(discord_id)
    return any(str(g["app_id"]) == str(appid) for g in games)


def main():
    if len(sys.argv) < 2:
        print("ERROR: usage: should_buy.py <game name> [member1] [member2] ...")
        return

    # DEBUG: marker to prove script executed
    print(f"[DEBUG] should_buy.py executed for: {sys.argv[1]}")

    # First arg is game name (quoted), rest are optional member names
    game_query = sys.argv[1]
    requested_members = sys.argv[2:]

    appid = search_steam(game_query)
    if not appid:
        print("NOT_FOUND")
        return

    # Rate limit before Steam API call
    ITAD_LIMITER.wait()
    
    details = fetch_steam_details(appid)
    game_name = details["name"] if details else game_query

    print(f"GAME: {game_name}")
    print(f"APPID: {appid}")
    print(f"STORE_URL: https://store.steampowered.com/app/{appid}/")

    # Co-op status
    is_coop, coop_modes = fetch_coop_status(appid)
    if is_coop:
        print(f"COOP: Yes | MODES: {coop_modes}")
    else:
        print("COOP: No")

    # Price
    prices = fetch_price(appid)
    retail = prices.get("current_retail") if prices else None
    hist_low = prices.get("historical_retail") if prices else None
    gg_url = prices.get("url", "") if prices else ""

    try:
        retail = float(retail) if retail is not None else None
        hist_low = float(hist_low) if hist_low is not None else None
    except (TypeError, ValueError):
        retail = hist_low = None

    if retail is not None:
        print(f"CURRENT_PRICE: €{retail:.2f}")
    else:
        print("CURRENT_PRICE: N/A")

    if hist_low is not None:
        print(f"HISTORICAL_LOW: €{hist_low:.2f}")
        if retail and retail <= hist_low * 1.05:
            print("PRICE_STATUS: AT_OR_NEAR_HISTORICAL_LOW")
        elif retail and hist_low > 0:
            above_pct = ((retail - hist_low) / hist_low) * 100
            print(f"PRICE_STATUS: {above_pct:.0f}% ABOVE HISTORICAL LOW")

    if gg_url:
        print(f"GG_DEALS_URL: {gg_url}")

    # Per-member ownership check
    all_users = get_linked_users()
    members = resolve_members(requested_members, all_users)

    if not members:
        print("NO_MEMBERS_FOUND")
        return

    print()
    owners = []
    buyers = []

    for u in members:
        name = ensure_display_name(u)
        if user_owns_game(u["discord_id"], appid):
            owners.append(name)
        else:
            buyers.append(name)

    for name in owners:
        print(f"OWNS: {name}")

    total_cost = 0.0
    for name in buyers:
        if retail is not None:
            print(f"NEEDS_TO_BUY: {name} | COST: €{float(retail):.2f}")
            total_cost += float(retail)
        else:
            print(f"NEEDS_TO_BUY: {name} | COST: N/A")

    if buyers and retail is not None:
        print(f"TOTAL_COST: €{total_cost:.2f} for {len(buyers)} member(s)")


if __name__ == "__main__":
    main()
