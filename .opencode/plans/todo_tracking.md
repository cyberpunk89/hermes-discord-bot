# Remaining Tasks & Tracking

This file tracks pending work for the game-price-bot project.

---

## Completed ✓

### Phase 1 & 2 Optimizations
- [x] Create `skills/_importer.py` - Centralized path config
- [x] Create `skills/_steam_utils.py` - Shared Steam utilities
- [x] Create `skills/_price_utils.py` - Shared price lookups
- [x] Create `skills/_rate_limiter.py` - API rate limiting
- [x] Create `db/cache.py` - Unified cache layer
- [x] Enable caching in scripts

### Features
- [x] Watchlist auto-cleanup on library refresh
- [x] Common-games formatting (5 limit, --all flag)
- [x] Game price button context (WATCHLIST_STATUS, OWNERSHIP_STATUS)
- [x] Enhanced Hermes personality (SOUL.md)
- [x] Custom personality switching (hermes, altair, friendly)

---

## Pending

### Priority 1: Known Issues

- [ ] **Personality switching** - Custom personalities not showing in `/personality` list
  - Status: File-based config applied, needs testing
  - Next: Test in Discord, may need config adjustment

- [ ] **Discord buttons** - Interactive buttons not appearing
  - Status: Skipped (needs Discord component handler)
  - Alternative: Text-based instructions in responses

### Priority 2: Improvements

- [ ] **File-based personality loading** - Test and verify working
- [ ] **Cache TTL tuning** - Could adjust based on usage patterns
- [ ] **Rate limiter defaults** - Currently conservative, could tune

### Priority 3: Nice to Have

- [ ] **Additional personalities** - Create more (e.g., Lorekeeper)
- [ ] **Unit tests** - Add test coverage for utilities
- [ ] **Error handling** - Standardize error messages

---

## Notes

### How to Update This File

When completing a task:
1. Change `[ ]` to `[x]`
2. Add date and optionally a note
3. Commit with descriptive message

Example:
```markdown
- [x] Task name (completed 2026-04-25)
```

### Testing Checklist

Run these commands to verify everything works:
```bash
# Core scripts
python3 skills/steam-link/scripts/steam_linker.py list-users
python3 skills/should-buy/scripts/should_buy.py "Hades"
python3 skills/common-games/scripts/common_games.py

# Refresh with cleanup
python3 skills/weekly-recap/scripts/refresh_playtime.py
```

---

## Questions & Decisions Needed

1. **Personality paths** - Use absolute paths or home-relative?
2. **Cache strategy** - Current TTLs OK or need tuning?
3. **Additional features** - What's priority for next session?