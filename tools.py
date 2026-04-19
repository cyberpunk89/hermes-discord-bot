import re
import requests
from cachetools import TTLCache

_cache = TTLCache(maxsize=200, ttl=1800)

STEAM_DETAIL_URL = "https://store.steampowered.com/api/appdetails"
STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
STEAM_DECK_API = "https://store.steampowered.com/promotion/v2/steamdeck/filter/"
GG_DEALS_URL = "https://api.gg.deals/v1/prices/by-steam-app-id/"
ITAD_BASE = "https://api.isthereanydeal.com"
PROTONDB_API = "https://protondb.max-p.me/api/v1/games"

_STEAM_APP_RE = re.compile(r"https?://store\.steampowered\.com/app/(\d+)", re.IGNORECASE)
_STEAM_SEARCH_RE = re.compile(r"^[\w\s\-:]+$")

_PROTON_RATING_MAP = {
    "platinum": "💎 Platinum",
    "gold": "🥇 Gold",
    "silver": "🥈 Silver",
    "bronze": "🥉 Bronze",
    "borked": "💀 Borked",
}

_DECK_STATUS_MAP = {
    "verified": "✅ Verified",
    "playable": "🔶 Playable",
    "unsupported": "❌ Unsupported",
}


def detect_steam_link(text: str) -> str | None:
    m = _STEAM_APP_RE.search(text)
    return m.group(1) if m else None


def is_search_query(text: str) -> bool:
    if detect_steam_link(text):
        return False
    text = text.strip()
    if not text or len(text) < 2:
        return False
    return True


def get_game_info(appid: str, gg_key: str, itad_key: str | None = None) -> dict | None:
    if appid in _cache:
        return _cache[appid]

    steam = _fetch_steam_details(appid)
    if not steam:
        return None

    gg_data = _get_gg_deals_price(appid, gg_key)

    if not gg_data and itad_key:
        gg_data = _get_itad_fallback(appid, itad_key)

    proton_data = _get_proton_rating(appid)
    deck_data = _get_steam_deck_status(appid)

    result = {
        "appid": appid,
        "title": steam.get("name"),
        "image": steam.get("header_image"),
        "store_url": f"https://store.steampowered.com/app/{appid}/",
        "release_date": steam.get("release_date", {}).get("date", ""),
        "platforms": _format_platforms(steam.get("platforms", {})),
        "developer": ", ".join(steam.get("developers", [])),
        "publisher": ", ".join(steam.get("publishers", [])),
        "genres": ", ".join(steam.get("genres", [])) if steam.get("genres") else "",
        "metacritic": steam.get("metacritic", {}).get("score") if steam.get("metacritic") else None,
        "steam_rating": steam.get("steam_rating"),
        "steam_reviews": steam.get("total_reviews"),
        "gg_deals_url": f"https://gg.deals/game/{steam.get('name', '').lower().replace(' ', '-')}/" if steam.get("name") else "",
        "current_retail": gg_data.get("current_retail") if gg_data else None,
        "current_retail_store": gg_data.get("current_retail_store") if gg_data else None,
        "current_retail_url": gg_data.get("current_retail_url") if gg_data else None,
        "current_keyshops": gg_data.get("current_keyshops") if gg_data else None,
        "historical_retail": gg_data.get("historical_retail") if gg_data else None,
        "historical_keyshops": gg_data.get("historical_keyshops") if gg_data else None,
        "currency": gg_data.get("currency") if gg_data else "EUR",
        "deals": gg_data.get("deals", []) if gg_data else [],
        "proton_rating": proton_data.get("rating") if proton_data else None,
        "proton_reports": proton_data.get("total") if proton_data else None,
        "steam_deck_status": deck_data.get("status") if deck_data else None,
    }

    _cache[appid] = result
    return result


def search_game(query: str, gg_key: str, itad_key: str | None = None) -> dict | None:
    cache_key = f"search:{query.lower()}"
    if cache_key in _cache:
        return _cache[cache_key]

    appid = _search_steam(query)
    if not appid:
        return None

    info = get_game_info(appid, gg_key, itad_key)
    if info:
        _cache[cache_key] = info
    return info


def _search_steam(query: str) -> str | None:
    try:
        r = requests.get(
            STEAM_SEARCH_URL,
            params={"term": query, "l": "english", "cc": "EU"},
            timeout=8,
        )
        data = r.json()
        items = data.get("items", [])
        if items:
            return str(items[0].get("id"))
    except Exception:
        pass
    return None


def _fetch_steam_details(appid: str) -> dict | None:
    try:
        r = requests.get(
            STEAM_DETAIL_URL,
            params={"appids": appid, "cc": "eu", "l": "en"},
            timeout=8,
        )
        data = r.json().get(str(appid), {})
        if not data.get("success"):
            return None
        d = data.get("data", {})
        return {
            "name": d.get("name"),
            "header_image": d.get("header_image"),
            "release_date": d.get("release_date", {}),
            "platforms": d.get("platforms", {}),
            "developers": d.get("developers", []),
            "publishers": d.get("publishers", []),
            "genres": [g.get("description") for g in d.get("genres", [])],
            "metacritic": d.get("metacritic"),
            "steam_rating": d.get("steam_rating"),
            "total_reviews": d.get("total_reviews"),
        }
    except Exception:
        return None


def _get_gg_deals_price(appid: str, key: str) -> dict | None:
    try:
        r = requests.get(
            GG_DEALS_URL,
            params={"ids": appid, "key": key, "region": "eu"},
            timeout=8,
        )
        data = r.json()
        item = data.get("data", {}).get(str(appid))
        if not item:
            return None

        prices = item.get("prices", {})
        gg_url = item.get("url", "")
        return {
            "current_retail": prices.get("currentRetail"),
            "current_retail_store": None,
            "current_retail_url": gg_url,
            "current_keyshops": prices.get("currentKeyshops"),
            "historical_retail": prices.get("historicalRetail"),
            "historical_keyshops": prices.get("historicalKeyshops"),
            "currency": prices.get("currency"),
            "url": gg_url,
            "deals": [],
        }
    except Exception:
        return None


def _get_itad_fallback(appid: str, key: str) -> dict | None:
    try:
        r = requests.get(
            f"{ITAD_BASE}/games/lookup/v1",
            params={"key": key, "appid": appid},
            timeout=8,
        )
        plain = r.json().get("game", {}).get("id")
        if not plain:
            return None

        r = requests.post(
            f"{ITAD_BASE}/games/prices/v3",
            params={"key": key, "country": "DE"},
            json=[plain],
            timeout=8,
        )
        items = r.json()
        if not items:
            return None

        item = items[0]
        deals = item.get("deals", [])
        current_retail = None
        current_retail_store = None
        current_retail_url = None
        current_keyshops = None
        if deals:
            best = min(deals, key=lambda d: d["price"]["amount"])
            current_retail = best["price"]["amount"]
            current_retail_store = best["shop"]["name"]
            current_retail_url = best["url"]

        low = item.get("historyLow", {}).get("all")
        historical_retail = low["amount"] if low else None

        return {
            "current_retail": current_retail,
            "current_retail_store": current_retail_store,
            "current_retail_url": current_retail_url,
            "current_keyshops": current_keyshops,
            "historical_retail": historical_retail,
            "historical_keyshops": None,
            "currency": "EUR",
            "deals": deals,
        }
    except Exception:
        return None


def _get_proton_rating(appid: str) -> dict | None:
    return None


def _get_steam_deck_status(appid: str) -> dict | None:
    return None


def _format_platforms(platforms: dict) -> str:
    result = []
    if platforms.get("windows"):
        result.append("Windows")
    if platforms.get("mac"):
        result.append("Mac")
    if platforms.get("linux"):
        result.append("Linux")
    return ", ".join(result)