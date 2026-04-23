#!/usr/bin/env python3
import sys
import os
import requests
import time

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills", "game-price", "scripts"))
import _load_env  # noqa: F401
os.environ.setdefault("DB_PATH", os.path.join(_PROJECT_DIR, "watchlist.db"))

from database import get_linked_users, get_user_games
from price_lookup import get_gg_price, get_itad_price

STEAMSPY_URL = "https://steamspy.com/api.php"
GG_KEY = os.environ.get("GG_DEALS_API_KEY", "")
ITAD_KEY = os.environ.get("ITAD_API_KEY", "")

MAX_PRICE_EUR = 60.0
CANDIDATES_TO_CHECK = 30
TARGET_SUGGESTIONS = 5


def get_owned_app_ids():
    users = get_linked_users()
    owned = set()
    for u in users:
        for g in get_user_games(u["discord_id"]):
            owned.add(str(g["app_id"]))
    return owned, len(users)


def parse_owners_lower_bound(owners_str):
    """SteamSpy owners field is '5,000,000 .. 10,000,000' — take lower bound."""
    try:
        return int(owners_str.split("..")[0].replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0


def fetch_coop_candidates():
    """Top 'Online Co-op' tagged games from SteamSpy, sorted by owner count."""
    try:
        r = requests.get(STEAMSPY_URL, params={"request": "tag", "tag": "Online Co-op"}, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"ERROR: SteamSpy unavailable ({e})", file=sys.stderr)
        return []

    candidates = []
    for appid, info in data.items():
        name = info.get("name", "").strip()
        if not name:
            continue
        owners = parse_owners_lower_bound(info.get("owners", "0"))
        candidates.append({"appid": appid, "name": name, "owners": owners})

    candidates.sort(key=lambda x: x["owners"], reverse=True)
    return candidates


def fetch_price(appid):
    prices = get_gg_price(appid) if GG_KEY else None
    if not prices and ITAD_KEY:
        prices = get_itad_price(appid)
    return prices


def main():
    owned_ids, user_count = get_owned_app_ids()
    print(f"LINKED_USERS: {user_count}")

    if user_count == 0:
        print("NO_USERS: No linked Steam accounts found. Use /skill steam-link first.")
        return

    candidates = fetch_coop_candidates()
    if not candidates:
        print("ERROR: Could not fetch suggestions from SteamSpy. Try again later.")
        return

    unowned = [c for c in candidates if c["appid"] not in owned_ids]

    suggestions = []
    checked = 0
    for c in unowned:
        if len(suggestions) >= TARGET_SUGGESTIONS or checked >= CANDIDATES_TO_CHECK:
            break
        checked += 1

        prices = fetch_price(c["appid"])
        if not prices:
            continue

        try:
            retail = float(prices["current_retail"]) if prices.get("current_retail") is not None else None
            hist_low = float(prices["historical_retail"]) if prices.get("historical_retail") is not None else None
        except (TypeError, ValueError):
            continue

        if retail is None or retail > MAX_PRICE_EUR:
            continue

        discount_pct = 0
        if hist_low and hist_low > 0 and retail < hist_low:
            discount_pct = int((1 - retail / hist_low) * 100)

        store_url = f"https://store.steampowered.com/app/{c['appid']}/"
        hist_str = f"€{hist_low:.2f}" if hist_low else "N/A"
        disc_str = f"{discount_pct}% off" if discount_pct > 0 else "full price"

        suggestions.append(
            f"SUGGESTION: {c['name']} | APPID: {c['appid']} | PRICE: €{retail:.2f}"
            f" | HIST_LOW: {hist_str} | DISCOUNT: {disc_str} | URL: {store_url}"
        )
        time.sleep(0.15)

    if not suggestions:
        print("NO_SUGGESTIONS: No priced co-op games found outside the group's library. Try again later.")
        return

    for line in suggestions:
        print(line)


if __name__ == "__main__":
    main()
