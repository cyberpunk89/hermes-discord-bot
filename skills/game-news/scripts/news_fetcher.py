#!/usr/bin/env python3
import sys
import os
import requests
from datetime import datetime

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
import _load_env  # noqa: F401
os.environ.setdefault("DB_PATH", os.path.join(_PROJECT_DIR, "watchlist.db"))
from database import get_common_games, is_news_seen, add_seen_news

STEAM_KEY = os.environ.get("STEAM_API_KEY", "")
STEAM_NEWS_URL = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
UPDATE_KEYWORDS = {"update", "patch", "hotfix", "new content", "season", "event", "dlc", "release"}


def is_relevant(title, contents):
    text = (title + " " + contents).lower()
    return any(kw in text for kw in UPDATE_KEYWORDS)


def fetch_news(app_id, game_name):
    try:
        r = requests.get(
            STEAM_NEWS_URL,
            params={"appid": app_id, "count": 10, "maxlength": 500, "format": "json"},
            timeout=10,
        )
        items = r.json().get("appnews", {}).get("newsitems", [])
        results = []
        for item in items:
            gid = item.get("gid", "")
            title = item.get("title", "")
            contents = item.get("contents", "")
            url = item.get("url", "")
            date = datetime.fromtimestamp(item.get("date", 0)).strftime("%Y-%m-%d")

            if is_news_seen(gid):
                continue
            if not is_relevant(title, contents):
                continue

            add_seen_news(app_id, gid, title)
            results.append({"game": game_name, "title": title, "url": url, "date": date, "summary": contents[:300]})
        return results
    except Exception:
        return []


def main():
    if len(sys.argv) > 1:
        app_id = int(sys.argv[1])
        games = [{"app_id": app_id, "game_name": f"App {app_id}"}]
    else:
        games = get_common_games()

    if not games:
        print("NEW_ITEMS: 0")
        return

    all_items = []
    for game in games:
        items = fetch_news(game["app_id"], game["game_name"])
        all_items.extend(items)

    print(f"NEW_ITEMS: {len(all_items)}")
    for item in all_items:
        print("---")
        print(f"GAME: {item['game']}")
        print(f"TITLE: {item['title']}")
        print(f"URL: {item['url']}")
        print(f"DATE: {item['date']}")
        print(f"SUMMARY: {item['summary']}")


if __name__ == "__main__":
    main()
