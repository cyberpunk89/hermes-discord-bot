#!/usr/bin/env python3
import sys
import os
import re
import requests

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
import _load_env  # noqa: F401

GG_KEY = os.environ.get("GG_DEALS_API_KEY", "")
ITAD_KEY = os.environ.get("ITAD_API_KEY", "")

STEAM_DETAIL_URL = "https://store.steampowered.com/api/appdetails"
STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
GG_DEALS_URL = "https://api.gg.deals/v1/prices/by-steam-app-id/"
ITAD_BASE = "https://api.isthereanydeal.com"
_STEAM_APP_RE = re.compile(r"https?://store\.steampowered\.com/app/(\d+)", re.IGNORECASE)


def detect_steam_link(text):
    m = _STEAM_APP_RE.search(text)
    return m.group(1) if m else None


def search_steam(query):
    try:
        r = requests.get(STEAM_SEARCH_URL, params={"term": query, "l": "english", "cc": "EU"}, timeout=8)
        items = r.json().get("items", [])
        return str(items[0]["id"]) if items else None
    except Exception:
        return None


def fetch_steam_details(appid):
    try:
        r = requests.get(STEAM_DETAIL_URL, params={"appids": appid, "cc": "eu", "l": "en"}, timeout=8)
        data = r.json().get(str(appid), {})
        if not data.get("success"):
            return None
        d = data["data"]
        return {
            "name": d.get("name"),
            "header_image": d.get("header_image"),
            "release_date": d.get("release_date", {}).get("date", ""),
            "developers": ", ".join(d.get("developers", [])),
            "publishers": ", ".join(d.get("publishers", [])),
            "genres": ", ".join(g["description"] for g in d.get("genres", [])),
            "metacritic": d.get("metacritic", {}).get("score") if d.get("metacritic") else None,
            "steam_rating": d.get("steam_rating", {}).get("rating") if d.get("steam_rating") else None,
            "total_reviews": d.get("total_reviews"),
        }
    except Exception:
        return None


def get_gg_price(appid, region="eu"):
    try:
        r = requests.get(GG_DEALS_URL, params={"ids": appid, "key": GG_KEY, "region": region}, timeout=8)
        item = r.json().get("data", {}).get(str(appid))
        if not item:
            return None
        prices = item.get("prices", {})
        return {
            "current_retail": prices.get("currentRetail"),
            "current_keyshops": prices.get("currentKeyshops"),
            "historical_retail": prices.get("historicalRetail"),
            "historical_keyshops": prices.get("historicalKeyshops"),
            "url": item.get("url", ""),
        }
    except Exception:
        return None


def get_itad_price(appid, country="DE"):
    try:
        r = requests.get(f"{ITAD_BASE}/games/lookup/v1", params={"key": ITAD_KEY, "appid": appid}, timeout=8)
        plain = r.json().get("game", {}).get("id")
        if not plain:
            return None
        r = requests.post(f"{ITAD_BASE}/games/prices/v3", params={"key": ITAD_KEY, "country": country}, json=[plain], timeout=8)
        items = r.json()
        if not items:
            return None
        deals = items[0].get("deals", [])
        best = min(deals, key=lambda d: d["price"]["amount"]) if deals else None
        low = items[0].get("historyLow", {}).get("all")
        return {
            "current_retail": best["price"]["amount"] if best else None,
            "current_keyshops": None,
            "historical_retail": low["amount"] if low else None,
            "historical_keyshops": None,
            "url": best["url"] if best else "",
        }
    except Exception:
        return None


def fetch_prices(appid, gg_region, itad_country):
    prices = get_gg_price(appid, region=gg_region)
    if not prices and ITAD_KEY:
        prices = get_itad_price(appid, country=itad_country)
    return prices


def main():
    if len(sys.argv) < 2:
        print("NO_RESULT")
        return

    args = sys.argv[1:]
    include_india = "--india" in args
    args = [a for a in args if a != "--india"]
    query = " ".join(args)

    appid = detect_steam_link(query) or search_steam(query)
    if not appid:
        print("NO_RESULT")
        return

    steam = fetch_steam_details(appid)
    if not steam:
        print("NO_RESULT")
        return

    prices = fetch_prices(appid, gg_region="eu", itad_country="DE")
    prices_in = fetch_prices(appid, gg_region="in", itad_country="IN") if include_india else None

    print(f"TITLE: {steam['name']}")
    print(f"APPID: {appid}")
    print(f"CURRENT_RETAIL: {prices['current_retail'] if prices and prices['current_retail'] else 'N/A'}")
    print(f"CURRENT_KEYSHOP: {prices['current_keyshops'] if prices and prices['current_keyshops'] else 'N/A'}")
    print(f"HIST_RETAIL: {prices['historical_retail'] if prices and prices['historical_retail'] else 'N/A'}")
    print(f"HIST_KEYSHOP: {prices['historical_keyshops'] if prices and prices['historical_keyshops'] else 'N/A'}")
    if include_india:
        print(f"CURRENT_RETAIL_IN: {prices_in['current_retail'] if prices_in and prices_in['current_retail'] else 'N/A'}")
        print(f"HIST_RETAIL_IN: {prices_in['historical_retail'] if prices_in and prices_in['historical_retail'] else 'N/A'}")
    print(f"STORE_URL: https://store.steampowered.com/app/{appid}/")
    print(f"GG_DEALS_URL: {prices['url'] if prices else 'N/A'}")
    print(f"DEVELOPER: {steam['developers']}")
    print(f"RELEASE_DATE: {steam['release_date']}")
    print(f"STEAM_RATING: {steam['steam_rating'] or 'N/A'}")
    print(f"METACRITIC: {steam['metacritic'] or 'N/A'}")
    print(f"GENRES: {steam['genres']}")


if __name__ == "__main__":
    main()
