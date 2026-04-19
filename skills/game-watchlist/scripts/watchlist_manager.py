#!/usr/bin/env python3
import sys
import os
import sqlite3
import requests

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills", "game-price", "scripts"))
import _load_env  # noqa: F401
os.environ.setdefault("DB_PATH", os.path.join(_PROJECT_DIR, "watchlist.db"))

from database import (
    add_to_watchlist, remove_from_watchlist, get_user_watchlist,
    set_target_price, count_user_watchlist, clear_user_watchlist,
    find_by_game_title, update_last_prices, get_all_watchlist,
)
from price_lookup import search_steam, get_gg_price, get_itad_price

MAX_WATCHLIST = 20
ITAD_KEY = os.environ.get("ITAD_API_KEY", "")
DB_PATH = os.environ.get("DB_PATH", os.path.join(_PROJECT_DIR, "watchlist.db"))


def resolve_user(discord_name: str) -> tuple[str | None, str]:
    if not discord_name:
        return None, discord_name
    name_lower = discord_name.lower()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT discord_id, discord_name FROM users WHERE LOWER(discord_name)=? LIMIT 1", (name_lower,)
        ).fetchone()
        if row:
            return row[0], row[1]
        row = conn.execute(
            "SELECT user_id, user_name FROM watchlist WHERE LOWER(user_name)=? LIMIT 1", (name_lower,)
        ).fetchone()
        if row:
            return row[0], row[1]
    return None, discord_name


def _require_user(discord_name: str) -> tuple[str, str] | None:
    discord_name = discord_name.strip()
    if not discord_name:
        print("ERROR: discord_name is empty — extract sender name from message prefix")
        return None
    discord_id, resolved_name = resolve_user(discord_name)
    if not discord_id:
        discord_id, resolved_name = discord_name, discord_name
    return discord_id, resolved_name


def _fetch_prices(appid):
    prices = get_gg_price(appid)
    if not prices and ITAD_KEY:
        prices = get_itad_price(appid)
    return prices


def cmd_add(args):
    if len(args) < 2:
        print("ERROR: add requires discord_name, game_name [target_price]")
        return
    discord_name, game_name = args[0], args[1]
    target = None
    if len(args) > 2:
        try:
            target = float(args[2])
        except ValueError:
            pass

    user = _require_user(discord_name)
    if not user:
        return
    discord_id, resolved_name = user

    if count_user_watchlist(discord_id) >= MAX_WATCHLIST:
        print(f"LIMIT_REACHED: {MAX_WATCHLIST}")
        return

    appid = search_steam(game_name)
    if not appid:
        print("NOT_FOUND")
        return

    try:
        r = requests.get("https://store.steampowered.com/api/appdetails", params={"appids": appid, "cc": "eu", "l": "en"}, timeout=8)
        title = r.json().get(str(appid), {}).get("data", {}).get("name", game_name)
    except Exception:
        title = game_name

    prices = _fetch_prices(appid)
    try:
        retail = float(prices["current_retail"]) if prices and prices.get("current_retail") is not None else None
        keyshop = float(prices["current_keyshops"]) if prices and prices.get("current_keyshops") is not None else None
    except (TypeError, ValueError):
        retail = keyshop = None

    success = add_to_watchlist(discord_id, resolved_name, appid, title, target_price=target)
    if success:
        if retail is not None:
            update_last_prices(appid, retail, keyshop)
        print(f"ADDED: {title}")
        print(f"APPID: {appid}")
        print(f"CURRENT_PRICE: {f'€{retail:.2f}' if retail is not None else 'N/A'}")
        if target:
            print(f"TARGET: €{target:.2f}")
    else:
        print("ALREADY_EXISTS")


def cmd_remove(args):
    if len(args) < 2:
        print("ERROR: remove requires discord_name, game_name")
        return
    discord_name, game_name = args[0], args[1]

    user = _require_user(discord_name)
    if not user:
        return
    discord_id, _ = user

    entry = find_by_game_title(discord_id, game_name)
    if not entry:
        print("NOT_FOUND")
        return
    remove_from_watchlist(discord_id, entry["appid"])
    print(f"REMOVED: {entry['game_title']}")


def cmd_list(args):
    if not args:
        print("ERROR: list requires discord_name")
        return

    user = _require_user(args[0])
    if not user:
        return
    discord_id, _ = user

    items = get_user_watchlist(discord_id)
    if not items:
        print("EMPTY")
        return

    print(f"COUNT: {len(items)}")
    for item in items:
        retail = item["last_retail_price"]
        if retail is None:
            prices = _fetch_prices(item["appid"])
            if prices:
                retail = prices.get("current_retail")
                keyshop = prices.get("current_keyshops")
                if retail is not None:
                    try:
                        retail = float(retail)
                        update_last_prices(item["appid"], retail, keyshop)
                    except (TypeError, ValueError):
                        retail = None
        try:
            current = f"€{float(retail):.2f}" if retail is not None else "N/A"
        except (TypeError, ValueError):
            current = "N/A"
        target = f"€{item['target_price']:.2f}" if item["target_price"] else "none"
        print(f"GAME: {item['game_title']} | PRICE: {current} | TARGET: {target}")


def cmd_set_target(args):
    if len(args) < 3:
        print("ERROR: set-target requires discord_name, game_name, price")
        return
    discord_name, game_name = args[0], args[1]
    try:
        price = float(args[2])
    except ValueError:
        print("ERROR: price must be a number")
        return

    user = _require_user(discord_name)
    if not user:
        return
    discord_id, _ = user

    entry = find_by_game_title(discord_id, game_name)
    if not entry:
        print("NOT_FOUND")
        return
    set_target_price(discord_id, entry["appid"], price)
    print(f"TARGET_SET: {entry['game_title']} → €{price:.2f}")


def cmd_check_prices(args):
    items = get_all_watchlist()
    if not items:
        print("NO_ITEMS")
        return
    processed = set()
    alerts = []
    for item in items:
        appid = item["appid"]
        if appid in processed:
            continue
        processed.add(appid)
        prices = _fetch_prices(appid)
        if not prices:
            continue
        retail = prices.get("current_retail")
        keyshop = prices.get("current_keyshops")
        if retail is None:
            continue
        update_last_prices(appid, retail, keyshop)
        last = item["last_retail_price"]
        target = item["target_price"]
        item_alerts = []
        if target and retail <= target:
            item_alerts.append(f"TARGET_HIT: €{retail} <= €{target}")
        if item["notify_any_drop"] and last and retail < last:
            drop_pct = ((last - retail) / last) * 100
            if drop_pct >= 10:
                item_alerts.append(f"PRICE_DROP: {drop_pct:.0f}% (€{last} → €{retail})")
        if item_alerts:
            alerts.append(f"USER:{item['user_id']} GAME:{item['game_title']} " + " | ".join(item_alerts))
    if alerts:
        print(f"ALERTS: {len(alerts)}")
        for a in alerts:
            print(a)
    else:
        print("NO_ALERTS")


def cmd_clear(args):
    if not args:
        print("ERROR: clear requires discord_name")
        return

    user = _require_user(args[0])
    if not user:
        return
    discord_id, _ = user

    count = clear_user_watchlist(discord_id)
    print(f"CLEARED: {count}")


def main():
    if len(sys.argv) < 2:
        print("ERROR: no command")
        return
    cmd = sys.argv[1]
    args = sys.argv[2:]
    {
        "add": cmd_add,
        "remove": cmd_remove,
        "list": cmd_list,
        "set-target": cmd_set_target,
        "check-prices": cmd_check_prices,
        "clear": cmd_clear,
    }.get(cmd, lambda _: print(f"ERROR: unknown command {cmd}"))(args)


if __name__ == "__main__":
    main()
