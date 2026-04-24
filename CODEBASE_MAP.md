# Codebase Dependency Map

This document maps critical files and their dependencies to prevent accidental deletion.

## Core Infrastructure (DO NOT DELETE)

### Database
- **`db/database.py`** — Central SQLite schema and all DB operations
  - Used by: ALL skills (game-watchlist, steam-link, common-games, game-news, weekly-recap, should-buy, game-suggest)
  - Tables: watchlist, price_history, users, user_games, seen_news, playtime_snapshots, game_coop_cache

### Shared Utilities
- **`skills/_load_env.py`** — Loads .env into os.environ for all skill scripts
  - Used by: Every skill script (via sys.path)
  - Critical for: API keys (DISCORD_BOT_TOKEN, STEAM_API_KEY, GG_DEALS_API_KEY, ITAD_API_KEY)

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
