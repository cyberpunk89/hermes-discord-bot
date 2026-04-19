---
name: game-watchlist
description: "Track game prices — list | add <game> [target €] | remove <game> | set-target <game> <price> | clear"
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

## Output Interpretation
- `ADDED: <title>` — success
- `ALREADY_EXISTS` — already in watchlist
- `NOT_FOUND` — game not found on Steam
- `LIMIT_REACHED` — 20 game max hit
- `EMPTY` — watchlist is empty
- `REMOVED: <title>` — removed
- `CLEARED: <n>` — n games cleared
- `ERROR: discord_name is empty` — extract sender name from message prefix

## Response Style
Stay in Hermes character. Adding = inducting into the price vigil. Listing = reading from the divine ledger.
