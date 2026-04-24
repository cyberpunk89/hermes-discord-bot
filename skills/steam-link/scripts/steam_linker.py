#!/usr/bin/env python3
import sys
import os
import json
import sqlite3

# Import centralized utilities
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _PROJECT_DIR)
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))

import _importer  # noqa: F401
import _load_env  # noqa: F401
from _steam_utils import resolve_vanity, fetch_library
from _rate_limiter import STEAM_LIMITER
from database import link_steam_user, unlink_steam_user, get_linked_users, upsert_user_games
from discord_utils import get_display_name, ensure_display_name

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


def cmd_link(args):
    if len(args) < 2:
        print("ERROR: link requires discord_name, steam_id_or_vanity")
        return

    # DEBUG: marker to prove script executed
    print(f"[DEBUG] steam_linker.py link executed")

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

    # Fetch fresh name from Discord API for accuracy
    resolved_name = get_display_name(discord_id)

    # Rate limit before Steam API call
    STEAM_LIMITER.wait()
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
        name = ensure_display_name(u)
        print(f"USER: {name} | STEAM: {u['steam_id']} | LINKED: {u['linked_at']}")


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
