---
name: game-watchlist
description: "Track game prices — list | add <game> [target €] | remove <game> | set-target <game> <price> | clear | check-prices"
version: 1.0.0
author: your-username
---

# Game Watchlist

## IMPORTANT
Always run the terminal command to perform the action. Never simulate results. Do not print or echo the terminal command in your response.

In a multi-user Discord channel, messages are prefixed `[Name]: message` — extract the name from that prefix and pass it as `<display_name>`. In a DM, use the `**User:**` field from the system prompt. Never pass an empty string.

## When no args given
If the user invokes with no arguments or just says "help", do NOT run any terminal command. Present this menu directly:

```
Available commands:
• list — show your watchlist with current prices
• add <game> [target €] — add a game, optionally with an alert price
• remove <game> — remove a game
• set-target <game> <price> — update the alert price for a game
• clear — remove all games from your watchlist
```

Stay in Hermes character when presenting this.

## Commands — run the matching one immediately

**Add a game:**
```
python3 <INSTALL_DIR>/skills/game-watchlist/scripts/watchlist_manager.py add "<display_name>" "<game name>" [target_price]
```

**Remove a game:**
```
python3 <INSTALL_DIR>/skills/game-watchlist/scripts/watchlist_manager.py remove "<display_name>" "<game name>"
```

**List watchlist:**
```
python3 <INSTALL_DIR>/skills/game-watchlist/scripts/watchlist_manager.py list "<display_name>"
```

**Set target price:**
```
python3 <INSTALL_DIR>/skills/game-watchlist/scripts/watchlist_manager.py set-target "<display_name>" "<game name>" <price>
```

**Clear watchlist:**
```
python3 <INSTALL_DIR>/skills/game-watchlist/scripts/watchlist_manager.py clear "<display_name>"
```

**Check all watchlist prices and fire alerts (used by cron):**
```
python3 <INSTALL_DIR>/skills/game-watchlist/scripts/watchlist_manager.py check-prices
```

## Output Interpretation
- `ADDED: <title>` — success
- `ALREADY_EXISTS` — already in watchlist
- `NOT_FOUND` — game not found on Steam
- `LIMIT_REACHED` — 20 game max hit
- `EMPTY` — watchlist is empty
- `REMOVED: <title>` — removed
- `CLEARED: <n>` — n games cleared
- `ERROR: discord_name is empty` — extract sender name from message prefix
- `NO_ALERTS` — prices checked, nothing triggered
- `ALERTS: <n>` — followed by alert lines:
  - `USER:<id> GAME:<title> TARGET_HIT: €<price> <= €<target>` — target price reached
  - `USER:<id> GAME:<title> PRICE_DROP: <pct>% (€<old> → €<new>)` — significant drop

## When running as a cron price check
If invoked by cron and `ALERTS: <n>` is in the output, post each alert to channel `PRICE_ALERT_CHANNEL_ID` from the env. Format each alert dramatically — target hit = the fates have delivered, price drop = a crack in the developer's armour. Mention the user by name (look them up from the USER id if needed).

## Response Style
Stay in Hermes character. Adding = inducting into the price vigil. Listing = reading from the divine ledger.

Always wrap every URL in angle brackets to suppress Discord embed previews: `<https://example.com>`. Never paste bare URLs.
