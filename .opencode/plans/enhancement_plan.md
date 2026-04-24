# Bot Enhancement Plan

## 1. Watchlist Auto-Cleanup (Library Games)

### Problem
Games already in a user's Steam library remain in their watchlist unnecessarily.

### Solution
- **On link:** When user links Steam account, check watchlist and auto-remove games they own
- **On refresh:** Run cleanup during `refresh_playtime` command
- **Optional:** Add `/skill watchlist clean` command to manually trigger

### Implementation
```python
# In steam_linker.py after fetching library:
def cleanup_watchlist(discord_id, owned_appids):
    conn = sqlite3.connect(DB_PATH)
    watchlist = conn.execute(
        "SELECT appid, game_title FROM watchlist WHERE user_id = ?", (discord_id,)
    ).fetchall()
    for appid, title in watchlist:
        if appid in owned_appids:
            conn.execute("DELETE FROM watchlist WHERE user_id = ? AND appid = ?", (discord_id, appid))
    conn.commit()
    return len(watchlist) - len(owned_appids)  # removed count
```

### Files to Modify
- `steam_linker.py` - Add cleanup after library fetch
- `refresh_playtime.py` - Optional cleanup trigger
- `watchlist_manager.py` - Optional manual cleanup command

---

## 2. Common Games Formatting

### Current Issue
Output is crowded with too much info on one line.

### Proposed Format
```
=== CO-OP LIBRARY (9 games) ===

🎮 Path of Exile 2
   537h total | 3 owners
   Modes: Online Multiplayer, Co-op, Online Co-op

🎮 Raft
   140h total | 3 owners
   Modes: Online Multiplayer, Co-op, Online Co-op

=== UNPLAYED GEMS (0 games) ===

=== OTHER COMMON (1 game) ===

⚔️ Graveyard Keeper
   0h total | 3 owners
   (No co-op support)
```

### Implementation
- Use emoji icons for visual separation
- Multi-line per game with better spacing
- Group modes into single line
- Add section dividers

### Files to Modify
- `common_games.py` - Format output with new structure

---

## 3. Interactive Buttons for Game Price

### Problem
Commands are text-only, no quick actions available.

### Solution
Add Discord message components (buttons) to price results:

```
🎮 Baldur's Gate 3
   €59.99 (Historical: €44.99)
   33% above historical low

[Add to Watchlist] [Remove from Watchlist] [Check Ownership]
```

### Implementation
```python
# In price_lookup.py or create wrapper
from discord.ext import commands

@commands.command()
async def game_price(ctx, game: str):
    # Fetch price data
    appid = search_steam(game)
    prices = get_gg_price(appid)
    
    # Build message with buttons
    embed = discord.Embed(title=game, color=0x3498db)
    embed.add_field(name="Price", value=f"€{prices['current_retail']}")
    
    # Add interactive buttons
    view = ButtonView()
    view.add_item(AddWatchlistButton(appid=appid, user_id=ctx.author.id))
    view.add_item(RemoveWatchlistButton(appid=appid, user_id=ctx.author.id))
    
    await ctx.send(embed=embed, view=view)
```

### Button Actions
- **Add to Watchlist:** If not in watchlist, add with current price
- **Remove from Watchlist:** If already in watchlist, remove it
- **Check Ownership:** Shows who owns the game (if Steam linked)
- **View Details:** Expand with more info (coop status, historical prices)

### Files to Modify
- `game-price/SKILL.md` - Add button instructions
- `price_lookup.py` - Add button handling
- Create `skills/_buttons.py` - Button class definitions

---

## 4. Enhanced Personality (Hermes)

### Current State
Personality is muted, could be more dramatic and in-character.

### Enhancement Strategy
1. **Update SOUL.md** with stronger voice examples
2. **Add personality layer** to all skill outputs
3. **Create response templates** for different scenarios

### Personality Rules to Add
```markdown
## Voice Guidelines
- Always speak as Hermes, the divine messenger of the gaming realm
- Use dramatic metaphors: "The gods have spoken!", "Fate has decreed..."
- Reference the user's Steam library as "your mortal collection"
- Price drops are "divine gifts", losses are "tragic inevitabilities"
- Never break character - even in errors

## Example Responses
- Price drop: "The heavens rejoice! Baldur's Gate 3 has descended to €44.99 - 
  a price worthy of the gods themselves!"
- Game owned: "Foolish mortal, you already possess this treasure!"
- Game news: "Word from the Steam gods arrives: A new patch has been revealed!"
- Weekly recap: "The spirits of the gaming realm have spoken - Nikel claimed 
  537 hours in Path of Exile 2, a testament to both dedication and madness!"
```

### Implementation
- Create `skills/_personality.py` - Helper functions for tone
- Update SOUL.md with enhanced examples
- Modify output formatting in all skills to use personality layer

### Files to Modify
- `~/.hermes/SOUL.md` - Main personality file
- `skills/_personality.py` - Create new utility
- All skill scripts - Add personality wrappers

---

## Implementation Priority

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| 🔴 P0 | Watchlist auto-cleanup | 1 hour | High (reduces clutter) |
| 🟡 P1 | Common games formatting | 1 hour | Medium (better UX) |
| 🟡 P1 | Game price buttons | 2 hours | High (interactivity) |
| 🟢 P2 | Enhanced personality | 2 hours | Medium (experience) |

**Total:** 6 hours for full implementation

---

## Technical Notes

### Watchlist Cleanup
- Run during Steam link (immediate benefit)
- Optional: Run on refresh_playtime (maintenance)
- Track cleanup count for user feedback

### Common Games
- Use emoji: 🎮 for co-op, ⚔️ for non-coop, 💎 for unplayed gems
- Add horizontal rules between sections
- Limit to 60 games max (already implemented)

### Game Price Buttons
- Requires Discord bot with component support
- Button IDs must be unique per message
- Handle button clicks in callback functions
- Cache button state (watchlist membership)

### Personality
- Update SOUL.md first (affects all responses)
- Create helper functions for tone consistency
- Test with each skill to ensure voice consistency

---

## Questions for You

1. **Watchlist cleanup:**
   - Should we auto-remove on link only, or also on refresh?
   - Should we show a message like "Removed 3 games you already own"?

2. **Common games format:**
   - Do you want to show game icons/images, or just emoji?
   - How many games per section max? (currently 60 total)

3. **Game price buttons:**
   - Which buttons do you want? (add/remove watchlist, check ownership, details)
   - Should buttons appear on all price lookups or just certain commands?

4. **Personality:**
   - Do you want Hermes to be MORE dramatic or just MORE present?
   - Any specific phrases/jokes you want added?
   - Should errors also be in character?

Let me know and I'll refine the plan before implementation!
