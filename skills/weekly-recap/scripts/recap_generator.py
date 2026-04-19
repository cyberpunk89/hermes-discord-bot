#!/usr/bin/env python3
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
import _load_env  # noqa: F401
os.environ.setdefault("DB_PATH", os.path.join(_PROJECT_DIR, "watchlist.db"))
from database import get_playtime_since_last_snapshot, save_playtime_snapshot, get_linked_users


def main():
    users = get_linked_users()
    if not users:
        print("NO_USERS")
        return

    deltas = get_playtime_since_last_snapshot()

    if not deltas:
        print("NO_DATA: First run — no snapshot to compare against. Run again next week.")
        save_playtime_snapshot()
        return

    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    print(f"PERIOD: {week_ago} to {today}")
    print(f"TOTAL_PLAYERS: {len(users)}")
    print()

    # Power rankings — total playtime per player
    player_totals = defaultdict(int)
    player_top_game = {}
    player_game_time = defaultdict(lambda: defaultdict(int))

    for row in deltas:
        name = row["discord_name"]
        game = row["game_name"]
        mins = row["delta_minutes"]
        player_totals[name] += mins
        player_game_time[name][game] += mins

    print("POWER_RANKINGS:")
    ranked = sorted(player_totals.items(), key=lambda x: x[1], reverse=True)
    for i, (name, mins) in enumerate(ranked, 1):
        hours = mins / 60
        top_game = max(player_game_time[name], key=player_game_time[name].get)
        print(f"RANK {i}: {name} | {hours:.1f}h | TOP_GAME: {top_game}")

    print()

    # Game of the week — most collective playtime
    game_totals = defaultdict(int)
    game_players = defaultdict(set)
    for row in deltas:
        game_totals[row["game_name"]] += row["delta_minutes"]
        game_players[row["game_name"]].add(row["discord_name"])

    if game_totals:
        top_game = max(game_totals, key=game_totals.get)
        top_hours = game_totals[top_game] / 60
        top_player_count = len(game_players[top_game])
        print(f"GAME_OF_THE_WEEK: {top_game} | {top_hours:.1f}h across {top_player_count} player(s)")

    print()

    # Top individual sessions
    print("TOP_SESSIONS:")
    top_rows = sorted(deltas, key=lambda r: r["delta_minutes"], reverse=True)[:10]
    for row in top_rows:
        hours = row["delta_minutes"] / 60
        print(f"{row['discord_name']}: {row['game_name']} — {hours:.1f}h")

    save_playtime_snapshot()


if __name__ == "__main__":
    main()
