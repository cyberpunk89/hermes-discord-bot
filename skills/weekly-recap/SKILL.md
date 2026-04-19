---
name: weekly-recap
description: Generate the weekly gaming power rankings and recap based on Steam playtime. Use when someone asks for the weekly recap or power rankings.
version: 1.0.0
author: your-username
---

# Weekly Recap & Power Rankings

## IMPORTANT
Run BOTH commands in order. Do not skip either. Do not make up playtime data. Do not print or echo the terminal commands in your response.

## Step 1 — Refresh playtime from Steam
```
python3 <INSTALL_DIR>/skills/weekly-recap/scripts/refresh_playtime.py
```

## Step 2 — Generate the recap
```
python3 <INSTALL_DIR>/skills/weekly-recap/scripts/recap_generator.py
```

## Output Interpretation
- `NO_USERS` — no Steam accounts linked yet
- `NO_DATA` — first run, baseline created for next week
- `POWER_RANKINGS:` → `RANK <n>: <name> | <hours>h | TOP_GAME: <game>`
- `GAME_OF_THE_WEEK: <game> | <hours>h across <n> player(s)`
- `TOP_SESSIONS:` → individual sessions

## Response Structure (in Hermes character)
1. **The Week in Review** — narrative summary
2. **Power Rankings** — colosseum standings per player
3. **Game of the Week** — dominant game
4. **Prophecy for Next Week** — dramatic prediction
