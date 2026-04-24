#!/usr/bin/env python3
import sys
import os
import re
import requests
from datetime import datetime

# Import centralized utilities
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _PROJECT_DIR)
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))

import _importer  # noqa: F401
import _load_env  # noqa: F401
from _rate_limiter import STEAM_LIMITER
from database import get_common_games, is_news_seen, add_seen_news
from cache import get_cache, set_cache

STEAM_NEWS_URL = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
UPDATE_KEYWORDS = {"update", "patch", "hotfix", "new content", "season", "event", "dlc", "release"}

# News cache TTL: 4 hours
NEWS_CACHE_TTL = 4 * 3600

_HTML_TAG = re.compile(r"<[^>]+>")
_BBCODE_TAG = re.compile(r"\[/?[a-z*]+(?:=[^\]]+)?\]", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")
_HTML_ENTITIES = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'", "&nbsp;": " "}


def clean_summary(text, max_len=250):
    for entity, char in _HTML_ENTITIES.items():
        text = text.replace(entity, char)
    text = _HTML_TAG.sub(" ", text)
    text = _BBCODE_TAG.sub(" ", text)
    text = _WHITESPACE.sub(" ", text).strip()
    if len(text) <= max_len:
        return text
    cut = text.rfind(" ", 0, max_len)
    return text[:cut if cut > 0 else max_len] + "…"


def is_relevant(title, contents):
    text = (title + " " + contents).lower()
    return any(kw in text for kw in UPDATE_KEYWORDS)


def fetch_news(app_id, game_name, recent_mode=False):
    try:
        # Rate limit before API call
        STEAM_LIMITER.wait()
        
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

            if not is_relevant(title, contents):
                continue
            if not recent_mode:
                if is_news_seen(gid):
                    continue
                add_seen_news(app_id, gid, title)

            results.append({"game": game_name, "title": title, "url": url, "date": date, "summary": clean_summary(contents)})
            if recent_mode and len(results) >= 3:
                break
        return results
    except Exception:
        return []


def main():
    args = sys.argv[1:]
    recent_mode = "--recent" in args
    args = [a for a in args if a != "--recent"]

    if args:
        app_id = int(args[0])
        games = [{"app_id": app_id, "game_name": f"App {app_id}"}]
    else:
        games = get_common_games()

    if not games:
        print("NEW_ITEMS: 0")
        return

    all_items = []
    for game in games:
        items = fetch_news(game["app_id"], game["game_name"], recent_mode=recent_mode)
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
