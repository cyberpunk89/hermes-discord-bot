# Game Price Bot - Remaining Tasks

## GitHub Issue Format (Copy to GitHub Issues)

```markdown
## 🚀 Feature: Game Price Bot Improvements

### Completed
- [x] Phase 1 optimizations (_importer, _steam_utils, _price_utils, _rate_limiter)
- [x] Phase 2 caching (db/cache.py integrated in all scripts)
- [x] Watchlist auto-cleanup on library refresh  
- [x] Common-games formatting with --all flag
- [x] Game price button context (WATCHLIST_STATUS, OWNERSHIP_STATUS)
- [x] Enhanced Hermes personality in SOUL.md
- [x] Custom personality switching (hermes, altair, friendly)

### In Progress
- [ ] Personality switching - custom personas not showing in /personality list

### Pending
- [ ] Discord buttons (needs component handler - lower priority)
- [ ] Additional personalities (optional)
- [ ] Unit tests (optional)

---

## 📝 Notes

### Testing
```bash
python3 skills/steam-link/scripts/steam_linker.py list-users
python3 skills/should-buy/scripts/should_buy.py "Hades"
python3 skills/common-games/scripts/common_games.py
python3 skills/weekly-recap/scripts/refresh_playtime.py
```

### Key Files
- `skills/_importer.py` - Centralized imports
- `skills/_steam_utils.py` - Steam API utilities  
- `skills/_price_utils.py` - Price lookup utilities
- `skills/_rate_limiter.py` - API rate limiting
- `db/cache.py` - Unified cache layer
- `~/.hermes/personalities/` - Custom personality files
- `.opencode/plans/todo_tracking.md` - Task tracking
```

### Quick Commands Reference

```bash
# Test all features
python3 skills/steam-link/scripts/steam_linker.py list-users
python3 skills/should-buy/scripts/should_buy.py "Baldur's Gate 3"
python3 skills/common-games/scripts/common_games.py
python3 skills/common-games/scripts/common_games.py --all
python3 skills/game-price/scripts/price_lookup.py "Hades"
python3 skills/weekly-recap/scripts/refresh_playtime.py
python3 skills/weekly-recap/scripts/recap_generator.py

# Gateway
sudo systemctl restart hermes-gateway
sudo systemctl status hermes-gateway

# Check cache
sqlite3 watchlist.db "SELECT * FROM api_cache"
```