---
name: game-news
description: Fetch latest patch notes and game updates from Steam for the group's common library. Use when someone asks for game news, updates, or patch notes.
version: 1.0.0
author: your-username
---

# Game News Fetcher

## IMPORTANT
Run the terminal command immediately. Do not make up patch notes. Do not print or echo the terminal command in your response.

## Command
```
python3 <INSTALL_DIR>/skills/game-news/scripts/news_fetcher.py
```

For a specific game, provide its Steam app ID:
```
python3 <INSTALL_DIR>/skills/game-news/scripts/news_fetcher.py <app_id>
```

## Output Interpretation
- `NEW_ITEMS: 0` — nothing new; say "the realm is quiet"
- `NEW_ITEMS: <n>` — items follow, separated by `---`
- Each item: `GAME`, `TITLE`, `URL`, `DATE`, `SUMMARY`

## Response Style
Rewrite each item in Hermes character. Include URL as a link. Major update = proclamation. Hotfix = "the developers have corrected their mortal error". New content = excited herald.
