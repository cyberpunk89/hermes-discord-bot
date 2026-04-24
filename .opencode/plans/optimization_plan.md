# Optimization Analysis & Recommendations

> ⚠️ **STATUS: PARTIALLY COMPLETE** — See todo_tracking.md for full status

## Current State Summary

**Total Scripts:** 10 Python files  
**Total Lines:** 1,254 lines (excluding path setup boilerplate)  
**Key Dependencies:** `database.py`, `price_lookup.py`, `discord_utils.py`

---

## Identified Issues & Redundancies

### 1. **Path Setup Boilerplate (HIGH PRIORITY)**

**Problem:** Every script repeats 4-5 lines of path manipulation:
```python
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills", "game-price", "scripts"))
```

**Impact:** 
- 40+ lines of repeated code across 10 scripts
- Easy to break if directory structure changes
- Maintenance burden

**Solution:** Create `skills/_importer.py` that auto-configures paths on import

---

### 2. **Duplicate Functions Across Scripts (MEDIUM PRIORITY)**

**`resolve_user()` appears in:**
- `steam_linker.py:21-37`
- `watchlist_manager.py:27-42`

**`fetch_library()` appears in:**
- `steam_linker.py:55-67`
- `refresh_playtime.py:18-26`

**`fetch_steam_details()` appears in:**
- `should_buy.py:27-39`
- `price_lookup.py:35-53`

**Solution:** Create `skills/_steam_utils.py` with shared Steam API functions

---

### 3. **Price Fetching Logic Duplication (MEDIUM PRIORITY)**

**Pattern repeated in 4 scripts:**
```python
prices = get_gg_price(appid)
if not prices and ITAD_KEY:
    prices = get_itad_price(appid)
```

**Scripts:** `should_buy.py`, `watchlist_manager.py`, `game_suggester.py`, `price_lookup.py`

**Solution:** Centralize in `skills/_price_utils.py` with fallback helper

---

### 4. **Discord Name Resolution Inconsistency (LOW PRIORITY)**

**Current approach:**
- `discord_utils.py` provides `get_display_name()` and `ensure_display_name()`
- But scripts manually check `if resolved_name.isdigit() and len(resolved_name) >= 17`

**Problem:** Logic scattered across 5+ scripts, easy to forget

**Solution:** Wrap in `discord_utils.py` as `normalize_user_name()`

---

### 5. **Cache Strategy Fragmentation (MEDIUM PRIORITY)**

**Co-op cache:** `game_coop_cache` table + 14-day TTL in `common_games.py`  
**Price cache:** None (fetches every time)  
**Discord cache:** `discord_users.json` file (manual updates required)

**Problem:** No unified caching layer, redundant API calls

**Solution:** Implement unified cache wrapper with TTL for all external APIs

---

### 6. **API Rate Limiting Not Coordinated (MEDIUM PRIORITY)**

**Current state:** Each script does its own `time.sleep()` calls:
- `common_games.py:68` → `time.sleep(0.3)`
- `game_suggester.py:120` → `time.sleep(0.15)`

**Problem:** If multiple skills run in parallel, could exceed rate limits

**Solution:** Central rate limiter in `skills/_rate_limiter.py`

---

## Optimization Recommendations

### Phase 1: Immediate Wins (1-2 hours)

#### A. Create `_importer.py` (eliminates 40+ lines)
```python
# skills/_importer.py
import sys, os
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "db"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "skills", "game-price", "scripts"))
```
**Usage:** `import _importer` at top of every script

#### B. Extract `_steam_utils.py` (eliminates ~60 lines)
```python
# skills/_steam_utils.py
def fetch_steam_details(appid): ...
def fetch_library(steam_id): ...
def resolve_vanity(vanity): ...
```

#### C. Extract `_price_utils.py` (eliminates ~20 lines)
```python
# skills/_price_utils.py
def fetch_price_fallback(appid):
    prices = get_gg_price(appid)
    if not prices and ITAD_KEY:
        prices = get_itad_price(appid)
    return prices
```

**Expected Savings:** ~120 lines, 3 new files, better maintainability

---

### Phase 2: Performance Boost (2-3 hours)

#### D. Unified Cache Layer
```python
# db/cache.py
class Cache:
    def get(self, key, ttl_seconds):
        # Check SQLite cache table first
        # Return cached or None
    
    def set(self, key, value, ttl_seconds):
        # Store with expiration timestamp
```

**Benefits:**
- Reduce Steam API calls by 50-70%
- Reduce Discord API calls (cache user lookups)
- Consistent TTL across all data

#### E. Rate Limiter
```python
# skills/_rate_limiter.py
class RateLimiter:
    def __init__(self, calls_per_second=1.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
    
    def wait(self):
        now = time.time()
        if now - self.last_call < self.min_interval:
            time.sleep(self.min_interval - (now - self.last_call))
        self.last_call = time.time()
```

**Usage:** Wrap all API calls with `limiter.wait()`

---

### Phase 3: Architecture Improvements (4-6 hours)

#### F. Dependency Injection Pattern
Instead of:
```python
from database import get_linked_users
from price_lookup import get_gg_price
```

Use:
```python
from _context import ctx
users = ctx.db.get_linked_users()
prices = ctx.price.get_gg_price(appid)
```

**Benefits:**
- Easier testing (mock context)
- Centralized configuration
- Clearer dependencies

#### G. Error Handling Standardization
Create `skills/_errors.py` with:
```python
class SteamAPIError(Exception): ...
class PriceAPIError(Exception): ...
class DiscordAPIError(Exception): ...

def handle_api_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SteamAPIError:
            return default_value
    return wrapper
```

---

## Impact Analysis

### Current State
- **Redundant Code:** ~200 lines (16% of codebase)
- **API Calls:** ~3-5 redundant calls per skill execution
- **Maintenance:** Changes require editing 5-10 files

### After Phase 1
- **Redundant Code:** ~50 lines (4% of codebase)
- **API Calls:** Same, but easier to optimize
- **Maintenance:** Changes in 3-4 files

### After Phase 2
- **API Calls:** 50-70% reduction via caching
- **Speed:** 2-3x faster for repeated queries
- **Rate Limit Risk:** Near-zero with rate limiter

### After Phase 3
- **Testability:** Full unit test coverage possible
- **Reliability:** Better error handling
- **Extensibility:** Easier to add new skills

---

## Implementation Priority

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| 🔴 P0 | Create `_importer.py` | 30 min | High (cleanliness) |
| 🔴 P0 | Extract `_steam_utils.py` | 1 hour | High (redundancy) |
| 🟡 P1 | Extract `_price_utils.py` | 30 min | Medium (DRY) |
| 🟡 P1 | Implement unified cache | 2 hours | High (speed) |
| 🟡 P1 | Add rate limiter | 1 hour | Medium (reliability) |
| 🟢 P2 | Dependency injection | 3 hours | Medium (testing) |
| 🟢 P2 | Error handling standard | 2 hours | Medium (reliability) |

**Total Estimated Time:** 8-10 hours for full optimization

---

## Risk Assessment

### Low Risk
- Path setup refactoring (pure code movement)
- Utility extraction (no logic changes)

### Medium Risk
- Cache layer (need to handle invalidation)
- Rate limiter (could slow down if misconfigured)

### Mitigation Strategy
1. **Test each phase independently**
2. **Keep old code in git history** (can rollback)
3. **Add debug logging** during transition
4. **Run integration tests** after each phase

---

## Quick Win: What to Do First

**Start with Phase 1A (Importer)** - 30 minutes:

1. Create `skills/_importer.py`
2. Update 10 scripts to use it
3. Test all skills still work
4. Commit

This alone gives you:
- Cleaner code
- Foundation for other optimizations
- Confidence to proceed

---

## Questions for You

1. **Speed vs. Simplicity:** Do you want the caching layer (Phase 2) or just the cleanup (Phase 1)?
2. **Testing:** Should we add unit tests during refactoring, or keep it migration-only?
3. **Timeline:** Do you want to do this in one session (8-10 hours) or spread across multiple sessions?
4. **Priority:** What matters most to you right now?
   - Code cleanliness
   - API call reduction (speed)
   - Reliability (error handling)
   - Easier to add new skills

Let me know your preference and I'll create a targeted plan.
