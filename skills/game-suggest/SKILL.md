---
name: game-suggest
description: "Suggest co-op games the group doesn't own yet, ranked by popularity and deal value."
version: 1.0.0
author: your-username
---

# Game Suggestions

## IMPORTANT
Run the terminal command immediately. Do not guess or make up suggestions. Do not print or echo the terminal command in your response.

## Command
```
python3 <INSTALL_DIR>/skills/game-suggest/scripts/game_suggester.py
```

## Output Interpretation
- `LINKED_USERS: <n>` — how many Steam accounts are linked
- `NO_USERS` — no one has linked their Steam account yet; tell them to use steam-link first
- `ERROR: ...` — something went wrong; relay the message briefly
- `NO_SUGGESTIONS` — couldn't find matches; tell them to try again later

Each suggestion is one line:
```
SUGGESTION: <Name> | APPID: <id> | PRICE: €<n> | HIST_LOW: €<n> | DISCOUNT: <n>% off | URL: <url>
```

## Response Style
Present the suggestions as Hermes' divine recommendations — co-op titles the mortal realm has overlooked. Frame each like a prophecy:
- On sale → "The fates have aligned. This window will not last."
- Full price → "The gods ask their due. Worth every coin."

Keep the list punchy: name, price, discount, and the store link. No walls of text.

Always wrap every URL in angle brackets to suppress Discord embed previews: `<https://example.com>`. Never paste bare URLs.
