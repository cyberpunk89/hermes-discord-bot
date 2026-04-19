---
name: common-games
description: Find games that all linked mortals own in common on Steam, sorted by collective playtime. Use when the group wants to know what they can play together.
version: 1.0.0
author: your-username
---

# Common Games Finder

## IMPORTANT
Run the terminal command immediately. Do not guess or make up a game list. Do not print or echo the terminal command in your response.

## Command
```
python3 <INSTALL_DIR>/skills/common-games/scripts/common_games.py
```

## Output Interpretation
- `LINKED_USERS: <n>` — how many Steam accounts are linked
- `NOT_ENOUGH_USERS` — fewer than 2 linked; tell them to use steam-link first
- `COMMON_COUNT: <n>` — number of shared games
- `GAME: <name> | PLAYTIME: <hours>h | OWNERS: <n>` — one line per game

## Response Style
Present top 10 games dramatically. High playtime = devoted. Low playtime = unplayed destiny.
