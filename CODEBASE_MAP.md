# Codebase Dependency Map

This document maps critical files and their dependencies to prevent accidental deletion.

## Core Infrastructure (DO NOT DELETE)

### Database
- **`db/database.py`** — Central SQLite schema and all DB operations
  - Used by: ALL skills (game-watchlist, steam-link, common-games, game-news, weekly-recap, should-buy, game-suggest)
  - Tables: watchlist, price_history, users, user_games, seen_news, playtime_snapshots, game_coop_cache, api_cache

### Shared Utilities
- **`skills/_load_env.py`** — Loads .env into os.environ for all skill scripts
  - Used by: Every skill script (via sys.path)
  - Critical for: API keys (DISCORD_BOT_TOKEN, STEAM_API_KEY, GG_DEALS_API_KEY, ITAD_API_KEY)

- **`skills/_importer.py`** — Centralized path configuration
  - Auto-configures sys.path for all skills
  - Eliminates repeated boilerplate in scripts

- **`skills/_steam_utils.py`** — Shared Steam API functions
  - Exports: `resolve_vanity()`, `fetch_library()`, `fetch_steam_details()`, `search_steam()`
  - Used by: steam_linker, refresh_playtime, should_buy

- **`skills/_price_utils.py`** — Shared price lookup utilities
  - Exports: `get_gg_price()`, `get_itad_price()`, `fetch_price_fallback()`
  - Used by: should_buy, watchlist_manager, game_suggester

- **`skills/_rate_limiter.py`** — Thread-safe API rate limiting
  - Exports: `STEAM_LIMITER`, `GG_DEALS_LIMITER`, `ITAD_LIMITER`, `DISCORD_LIMITER`
  - Prevents API rate limit violations

### Discord User Utilities
- **`db/discord_utils.py`** — Discord user name resolution (cache + API)
  - Exports: `get_display_name()`, `ensure_display_name()`
  - Uses: `db/cache.py` for 24-hour cache
  - Used by: All skills that display user names (steam-link, should-buy, weekly-recap, etc.)
- **`db/discord_users.json`** — Static Discord user data (fallback)

### Cache Layer
- **`db/cache.py`** — Unified SQLite cache with TTL expiration
  - Exports: `get_cache()`, `set_cache()`, `delete_cache()`, `clear_expired_cache()`, `init_cache_table()`
  - Used by: price_lookup, common_games, discord_utils, game-news
  - Cache TTLs: prices 1h, Steam 24h, co-op 14 days, Discord 24h, news 4h

### Price Lookups
- **`skills/game-price/scripts/price_lookup.py`** — Steam/GG.deals/ITAD API functions
  - Exports: `search_steam()`, `get_gg_price()`, `get_itad_price()`
  - Used by: game-watchlist, should-buy, game-suggest

### Co-op Detection
- **`skills/common-games/scripts/common_games.py`** — Fetches Steam co-op metadata
  - Exports: `fetch_coop_status()`
  - Used by: should-buy, game-suggest

## Required Configuration Files (DO NOT DELETE)

- **`.env`** — Runtime environment variables (API keys, Discord tokens, channel IDs)
  - Gitignored but REQUIRED for bot operation
  - Do not delete manually; recreate from `.env.example` if lost

- **`.env.example`** — Template for .env (safe to keep)
  - Gittracked, use as reference for required keys

## Skills Directory Structure

All skills follow this pattern:
```
skills/<skill-name>/
├── SKILL.md              # LLM instructions
├── scripts/
│   └── *.py             # Implementation
└── __pycache__/         # Auto-generated, safe to delete
```

## Deleted Legacy Files (Do NOT Restore)

These were successfully removed in commit `bf1462f`:
- ~~`main.py`~~ — Old discord.py bot (replaced by Hermes Agent)
- ~~`watchlist.py`~~ — Old watchlist handler (replaced by game-watchlist skill)
- ~~`tools.py`~~ — Old game lookup utilities (replaced by price_lookup.py)
- ~~`database.py`~~ (root) — Duplicate of `db/database.py`

## Cross-Skill Dependencies

These imports ensure skills work together:

```
watchlist_manager.py
  ├── from database import (add_to_watchlist, ...)
  └── from price_lookup import (search_steam, get_gg_price, get_itad_price)

should_buy.py
  ├── from database import (get_linked_users, ...)
  ├── from price_lookup import (search_steam, get_gg_price, get_itad_price)
  └── from common_games import (fetch_coop_status)

game_suggester.py
  ├── from database import (get_linked_users, ...)
  └── from price_lookup import (get_gg_price, get_itad_price)

news_fetcher.py
  ├── from database import (get_common_games, is_news_seen, add_seen_news)

recap_generator.py, refresh_playtime.py
  ├── from database import (get_playtime_since_last_snapshot, ...)
```

All scripts manage sys.path in their header to ensure imports work:
```python
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
```

## Safe to Delete (Auto-Generated)

- `__pycache__/` — Python bytecode cache
- `.pyc` files
- `*.log` — Runtime logs (except keep as reference)

## Deployment Checklist

Before any deletion:
1. Check this map for dependencies
2. Verify with `grep -r "filename"` across skills/
3. Verify in git history: `git log --all --full-history -- filename`
4. Ask before deleting any `.py` or `.env` files
