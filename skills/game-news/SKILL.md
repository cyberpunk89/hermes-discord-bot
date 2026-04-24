---
name: game-news
description: Fetch latest patch notes and game updates from Steam for the group's common library. Use when someone asks for game news, updates, or patch notes.
version: 1.0.0
author: your-username
---

# Game News Fetcher

## MANDATORY — DO NOT SKIP

**YOU MUST RUN THE SCRIPT FIRST. This is not optional.**

1. Run the terminal command BEFORE responding
2. The script output MUST appear in your response
3. DO NOT make up patch notes — use ONLY script output
4. If the script fails, state the error clearly

**Failure to run the script will result in incorrect responses.**

## IMPORTANT
Run the terminal command immediately. Do not make up patch notes. Do not print or echo the terminal command in your response.

## Command

**When a user manually asks for game news** — use `--recent` so browsing doesn't consume the cron feed:
```
python3 /home/nikel/Documents/projects/discord/game-price-bot/skills/game-news/scripts/news_fetcher.py --recent
```

For a specific game (manual, by Steam app ID):
```
python3 /home/nikel/Documents/projects/discord/game-price-bot/skills/game-news/scripts/news_fetcher.py --recent <app_id>
```

**When invoked by cron** — omit `--recent` so items are marked seen and won't re-post:
```
python3 /home/nikel/Documents/projects/discord/game-price-bot/skills/game-news/scripts/news_fetcher.py
```

## Output Interpretation
- `NEW_ITEMS: 0` — nothing new; say "the realm is quiet"
- `NEW_ITEMS: <n>` — items follow, separated by `---`
- Each item: `GAME`, `TITLE`, `URL`, `DATE`, `SUMMARY`

## Response Style

Use this exact format for each item, with a blank line between items:

```
**{GAME}** — {TITLE}
{1–2 sentences in Hermes character summarising what changed}
{DATE} · <{URL}>
```

Tone by update type:
- Patch / hotfix → dry, matter-of-fact with one cutting remark ("The gods corrected their error. It took them three weeks.")
- Major update / new content → excited herald energy, one punchy line of hype
- Event / season → treat as political intrigue from Olympus

If there are multiple items for the same game, group them together under one game header rather than repeating the name.

Never paste bare URLs — always wrap in angle brackets: `<https://example.com>`.
