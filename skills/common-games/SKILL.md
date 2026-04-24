---
name: common-games
description: Find co-op games all linked mortals own in common, highlighting unplayed gems as "pick something new" recommendations. Use when the group wants to know what they can play together.
version: 1.0.0
author: your-username
---

# Common Games Finder

## MANDATORY — DO NOT SKIP

**YOU MUST RUN THE SCRIPT FIRST. This is not optional.**

1. Run the terminal command BEFORE responding
2. The script output MUST appear in your response
3. DO NOT make up game lists — use ONLY script output
4. If the script fails, state the error clearly

**Failure to run the script will result in incorrect responses.**

## IMPORTANT
Run the terminal command immediately. Do not guess or make up a game list. Do not print or echo the terminal command in your response.

## Command
```
python3 /home/nikel/Documents/projects/discord/game-price-bot/skills/common-games/scripts/common_games.py
```

## Output Interpretation
- `LINKED_USERS: <n>` — how many Steam accounts are linked
- `NOT_ENOUGH_USERS` — only 1 user linked; tell them to use steam-link first
- `COMMON_COUNT: <n>` — total shared games
- `UNPLAYED_GEMS: <n>` — co-op games nobody has launched yet
- `COOP_PLAYED: <n>` — co-op games with some playtime
- `NON_COOP: <n>` — common games that aren't co-op

Three sections follow, each preceded by a `SECTION:` header:
- `SECTION: UNPLAYED_GEMS` → co-op games, zero playtime — these are the pick-something-new recommendations
- `SECTION: COOP_LIBRARY` → co-op games already played together
- `SECTION: OTHER_COMMON` → non-co-op shared games

Game line format: `GAME: <name> | PLAYTIME: <hours>h | OWNERS: <n> | MODE: <co-op type>`
(UNPLAYED_GEMS lines omit PLAYTIME since it's always 0)

## Response Style
Lead with UNPLAYED_GEMS as the divine recommendations — "titles the fates have reserved for your first adventure together." Frame each as destiny waiting to be fulfilled.

For COOP_LIBRARY: acknowledge the history, note what's left to explore.
Skip OTHER_COMMON unless asked — focus on what they can actually play together.

Always wrap every URL in angle brackets to suppress Discord embed previews: `<https://example.com>`. Never paste bare URLs.
