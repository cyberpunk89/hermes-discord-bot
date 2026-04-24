import os
import json
import requests

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_API = "https://discord.com/api/v10"

# Discord user cache TTL: 24 hours
DISCORD_CACHE_TTL = 24 * 3600

try:
    from cache import get_cache, set_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


def load_discord_users():
    cache_path = os.path.join(_PROJECT_DIR, "db", "discord_users.json")
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)
    return {}


def fetch_discord_user(discord_id):
    # Check cache first
    if CACHE_AVAILABLE:
        cache_key = f"discord_user_{discord_id}"
        cached = get_cache(cache_key, ttl_seconds=DISCORD_CACHE_TTL)
        if cached:
            return cached.get("username"), cached.get("global_name")

    if not DISCORD_TOKEN or not discord_id:
        return None, None
    try:
        r = requests.get(
            f"{DISCORD_API}/users/{discord_id}",
            headers={"Authorization": f"Bot {DISCORD_TOKEN}"},
            timeout=5,
        )
        if r.status_code == 200:
            data = r.json()
            username = data.get("username")
            global_name = data.get("global_name")

            # Cache the result
            if CACHE_AVAILABLE and username:
                set_cache(cache_key, {"username": username, "global_name": global_name}, ttl_seconds=DISCORD_CACHE_TTL)

            return username, global_name
    except Exception:
        pass
    return None, None


def get_display_name(discord_id):
    if not discord_id:
        return "Unknown"
    users = load_discord_users()
    if str(discord_id) in users:
        user = users[str(discord_id)]
        return user.get("global_name") or user.get("username") or str(discord_id)
    username, global_name = fetch_discord_user(discord_id)
    return global_name or username or str(discord_id)


def ensure_display_name(user_dict):
    name = user_dict.get("discord_name")
    if not name or (name.isdigit() and len(name) >= 17):
        return get_display_name(user_dict.get("discord_id"))
    return name