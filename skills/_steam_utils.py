"""
Shared Steam API utilities.
Centralizes Steam API calls to reduce duplication across scripts.
"""
import os
import requests

STEAM_KEY = os.environ.get("STEAM_API_KEY", "")
STEAM_BASE = "https://api.steampowered.com"
STEAM_DETAIL_URL = "https://store.steampowered.com/api/appdetails"
STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"


def resolve_vanity(vanity: str) -> str | None:
    """Resolve Steam vanity URL to numeric SteamID."""
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


def fetch_library(steam_id: str) -> list[dict] | None:
    """Fetch user's Steam library. Returns None if private/error."""
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
        return [
            {"appid": g["appid"], "name": g.get("name", "Unknown"), "playtime_forever": g.get("playtime_forever", 0)}
            for g in games
        ]
    except Exception:
        return None


def fetch_steam_details(appid: str) -> dict | None:
    """Fetch Steam game details (name, header_image)."""
    try:
        r = requests.get(STEAM_DETAIL_URL, params={"appids": appid, "cc": "eu", "l": "en"}, timeout=8)
        data = r.json().get(str(appid), {})
        if not data.get("success"):
            return None
        d = data["data"]
        return {
            "name": d.get("name", "Unknown"),
            "header_image": d.get("header_image", ""),
        }
    except Exception:
        return None


def search_steam(query: str) -> str | None:
    """Search Steam store for game, return appid."""
    try:
        r = requests.get(STEAM_SEARCH_URL, params={"term": query, "l": "english", "cc": "EU"}, timeout=8)
        items = r.json().get("items", [])
        return str(items[0]["id"]) if items else None
    except Exception:
        return None
