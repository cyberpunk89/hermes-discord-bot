import sys
import os
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
import _load_env  # noqa: F401
os.environ.setdefault("DB_PATH", os.path.join(_PROJECT_DIR, "watchlist.db"))
from database import (
    add_to_watchlist, remove_from_watchlist, get_user_watchlist, get_all_watchlist,
    update_last_prices, set_target_price, toggle_notification, count_user_watchlist,
    clear_user_watchlist, find_by_game_title, link_steam_user, unlink_steam_user,
    get_linked_users, upsert_user_games, get_user_games, get_common_games,
    is_news_seen, add_seen_news, save_playtime_snapshot, get_playtime_since_last_snapshot,
)
