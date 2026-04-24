"""
Shared price lookup utilities.
Centralizes GG.deals + ITAD fallback logic to reduce duplication.
"""
import os

GG_KEY = os.environ.get("GG_DEALS_API_KEY", "")
ITAD_KEY = os.environ.get("ITAD_API_KEY", "")

ITAD_BASE = "https://api.isthereanydeal.com"


def get_gg_price(appid: str, region: str = "eu") -> dict | None:
    """Fetch price from GG.deals API."""
    try:
        from skills.game_price.scripts.price_lookup import GG_DEALS_URL
        import requests

        r = requests.get(
            GG_DEALS_URL,
            params={"ids": appid, "key": GG_KEY, "region": region},
            timeout=8,
        )
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


def get_itad_price(appid: str, country: str = "DE") -> dict | None:
    """Fetch price from IsThereAnyDeal API."""
    try:
        import requests

        r = requests.get(f"{ITAD_BASE}/games/lookup/v1", params={"key": ITAD_KEY, "appid": appid}, timeout=8)
        plain = r.json().get("game", {}).get("id")
        if not plain:
            return None
        r = requests.post(
            f"{ITAD_BASE}/games/prices/v3", params={"key": ITAD_KEY, "country": country}, json=[plain], timeout=8
        )
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


def fetch_price_fallback(appid: str, gg_region: str = "eu", itad_country: str = "DE") -> dict | None:
    """
    Fetch price with GG.deals primary, ITAD fallback.
    Returns None if both fail.
    """
    prices = get_gg_price(appid, region=gg_region)
    if not prices and ITAD_KEY:
        prices = get_itad_price(appid, country=itad_country)
    return prices
