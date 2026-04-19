#!/usr/bin/env python3
import sys
import os

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
import _load_env  # noqa: F401
os.environ.setdefault("DB_PATH", os.path.join(_PROJECT_DIR, "watchlist.db"))
from database import get_common_games, get_linked_users


def main():
    users = get_linked_users()
    print(f"LINKED_USERS: {len(users)}")

    if len(users) < 2:
        print("NOT_ENOUGH_USERS")
        return

    games = get_common_games()
    print(f"COMMON_COUNT: {len(games)}")

    for g in games[:25]:
        hours = g["total_playtime"] // 60
        print(f"GAME: {g['game_name']} | PLAYTIME: {hours}h | OWNERS: {g['owner_count']}")


if __name__ == "__main__":
    main()
