#!/usr/bin/env python3
import sys
import os
import sqlite3
import requests

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
import _load_env  # noqa: F401
os.environ.setdefault("DB_PATH", os.path.join(_PROJECT_DIR, "watchlist.db"))
from database import link_steam_user, unlink_steam_user, get_linked_users, upsert_user_games

STEAM_KEY = os.environ.get("STEAM_API_KEY", "")
STEAM_BASE = "https://api.steampowered.com"
DB_PATH = os.environ.get("DB_PATH", os.path.join(_PROJECT_DIR, "watchlist.db"))


def resolve_user(discord_name: str) -> tuple[str | None, str]:
    """Resolve Discord display name to (discord_id, discord_name)."""
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


def resolve_vanity(vanity):
    try:
        r = requests.get(
            f"{STEAM_BASE}/ISteamUser/ResolveVanityURL/v1/",
            params={"key": STEAM_KEY, "vanityurl": vanity},
            timeout=8,
        )
        data = r.json().get("response", {})
        if data.get("success") == 1:
            return data["steamid"]
    except Exception:
        pass
    return None


def fetch_library(steam_id):
    try:
        r = requests.get(
            f"{STEAM_BASE}/IPlayerService/GetOwnedGames/v1/",
            params={"key": STEAM_KEY, "steamid": steam_id, "include_appinfo": 1, "include_played_free_games": 1},
            timeout=15,
        )
        response = r.json().get("response", {})
        # Steam omits 'game_count' entirely when the library is private
        if "game_count" not in response and not response.get("games"):
            return None
        games = response.get("games", [])
        return [{"appid": g["appid"], "name": g.get("name", "Unknown"), "playtime_forever": g.get("playtime_forever", 0)} for g in games]
    except Exception:
        return None


def cmd_link(args):
    if len(args) < 2:
        print("ERROR: link requires discord_name, steam_id_or_vanity")
        return
    # Accept either 2 args (display_name, steam_id) or 3 args (discord_id, display_name, steam_id)
    if len(args) >= 3:
        discord_name, steam_input = args[1].strip(), args[2]
    else:
        discord_name, steam_input = args[0].strip(), args[1]

    if not discord_name:
        print("ERROR: discord_name is empty — extract sender name from message prefix")
        return

    discord_id, resolved_name = resolve_user(discord_name)
    if not discord_id:
        discord_id, resolved_name = discord_name, discord_name

    steam_id = steam_input if steam_input.isdigit() and len(steam_input) >= 15 else resolve_vanity(steam_input)
    if not steam_id:
        print("VANITY_NOT_FOUND")
        return

    games = fetch_library(steam_id)
    if games is None:
        print("LIBRARY_PRIVATE_OR_ERROR")
        return

    link_steam_user(discord_id, resolved_name, steam_id)
    upsert_user_games(discord_id, games)
    print(f"LINKED: {resolved_name}")
    print(f"STEAM_ID: {steam_id}")
    print(f"GAME_COUNT: {len(games)}")


def cmd_unlink(args):
    if not args:
        print("ERROR: unlink requires discord_name")
        return
    discord_name = args[0].strip()
    if not discord_name:
        print("ERROR: discord_name is empty — extract sender name from message prefix")
        return

    discord_id, _ = resolve_user(discord_name)
    if not discord_id:
        discord_id = discord_name

    unlink_steam_user(discord_id)
    print("UNLINKED")


def cmd_list_users(args):
    users = get_linked_users()
    if not users:
        print("NO_USERS")
        return
    print(f"COUNT: {len(users)}")
    for u in users:
        print(f"USER: {u['discord_name']} | STEAM: {u['steam_id']} | LINKED: {u['linked_at']}")


def main():
    if len(sys.argv) < 2:
        print("ERROR: no command")
        return
    cmd = sys.argv[1]
    args = sys.argv[2:]
    {"link": cmd_link, "unlink": cmd_unlink, "list-users": cmd_list_users}.get(
        cmd, lambda _: print(f"ERROR: unknown command {cmd}")
    )(args)


if __name__ == "__main__":
    main()
