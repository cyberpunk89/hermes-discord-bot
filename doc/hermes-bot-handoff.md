# Hermes Discord Bot — Project Handoff

> **For:** Claude Code / OpenCode  
> **Project:** Hermes — a Discord bot with the personality of Hermes from Hades, powered by the Hermes LLM agent framework  
> **Owner:** Ninad (NJ Design)

---

## Project Vision

Build a Discord bot named **Hermes** (inspired by Hermes from the game *Hades*) for a co-op gaming friend group. The bot has a distinct personality — part snarky sports commentator, part dramatic lore narrator — and serves as the group's AI-powered gaming companion.

### Core Pillars

1. **Persistent AI personality** — Hermes lives in the server and speaks in character at all times
2. **Steam library integration** — Pulls game libraries from consenting users via Steam API
3. **Co-op game detection** — Identifies games the group owns in common
4. **Game news & update delivery** — Monitors and delivers patch notes / updates in Hermes' voice
5. **Weekly recaps & power rankings** — Generates dramatic, funny summaries of the group's gaming activity

---

## Personality Brief

Hermes speaks like a mix of:
- **Snarky sports commentator** — hot takes, play-by-play energy, mock outrage at bad decisions
- **Dramatic lore narrator** — treats gaming sessions as ancient prophecies, frames wins/losses as epic sagas

**Tone examples:**
- Game update: *"Hear ye, mortals. The developers of Deep Rock Galactic have once again meddled with fate. Patch 1.38 brings changes to the Scout that even I couldn't have foreseen..."*
- Weekly recap: *"Another week passes in the mortal realm. Ninad led the charge in three sessions, yet somehow managed to die first in all of them. The prophecy remains... unclear."*
- Power rankings: *"Standing before the gods this week: [Player] sits at the throne, [Player] languishes in the underworld. As it was written, so it shall be."*

**Key rules for the LLM prompt:**
- Never break character unless explicitly told to
- Always address users as "mortals" or by name
- Treat game updates as divine proclamations
- Frame losses dramatically, wins triumphantly but with caveats
- Keep responses concise — punchy, not essays

---

## Technical Architecture

```
Discord Bot (discord.py)
        ↓
Hermes Agent (LLM Framework)
        ├── Personality layer (system prompt)
        ├── Tool: Steam API (library fetch, playtime data)
        ├── Tool: Game news fetcher (RSS/web scrape per game)
        ├── Tool: Session memory (recent activity context)
        └── Tool: Recap generator
        ↓
Data Layer
        ├── SQLite DB (user profiles, sessions, game lists)
        ├── Scheduled tasks (news checks, weekly recap)
        └── Consent & opt-in store
```

---

## Feature Specifications

### 1. User Onboarding & Steam Consent

**Command:** `/link_steam <steam_id_or_vanity_url>`

- User explicitly opts in by linking their Steam profile
- Bot fetches their public game library via Steam API
- Stores: `user_id`, `steam_id`, `display_name`, `library[]`, `playtime{}`
- Hermes responds in character upon linking

**Notes:**
- Only fetch public libraries (Steam privacy settings respected)
- Store consent timestamp
- Command to unlink: `/unlink_steam`

---

### 2. Co-op Game Detection

**Command:** `/common_games [@mention @mention ...]` or auto on group join

- Compares libraries across linked users
- Filters to co-op capable games (use Steam store tags or a manual curated list)
- Returns games everyone owns, sorted by hours played collectively

**Hermes output example:**
> *"The fates have aligned, mortals. You all possess Deep Rock Galactic, Valheim, and Lethal Company. The question is whether you have the fortitude to actually launch one."*

---

### 3. Game News & Update Monitoring

**Trigger:** Scheduled background task (check every few hours)

**Sources per game (priority order):**
1. Steam news API: `https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={appid}`
2. RSS feeds from official game sites (fallback)

**Flow:**
- Fetch latest news for all games in the group's common library
- Filter for patch notes / update posts (keyword match: "update", "patch", "hotfix", "new content")
- Deduplicate (don't re-post already-seen items — store `last_seen_gid` per game)
- Pass to Hermes agent to rewrite in character
- Post to a designated `#game-news` channel

**Hermes framing for news:**
- Major update → dramatic proclamation
- Hotfix → dismissive sigh ("the developers have... corrected their mortal error")
- New content → excited herald

---

### 4. Weekly Recap & Power Rankings

**Trigger:** Scheduled task (Sunday evening, configurable)

**Data sources:**
- Steam recent playtime (per user, per game)
- Session logs if tracked manually
- Message activity in gaming channels (optional)

**Recap structure:**
1. **The Week in Review** — narrative summary of what the group played
2. **Power Rankings** — who played most, who carried, who dragged the team
3. **Game of the Week** — most played game collectively
4. **Prophecy for Next Week** — Hermes' dramatic prediction

**Command to trigger manually:** `/weekly_recap`

---

### 5. Ambient Personality (Optional / Phase 2)

- Hermes reacts to certain keywords in chat (e.g., mention of a game name → comment)
- Randomly chimes in during active gaming discussions (rate-limited, not spammy)
- Responds to direct `@Hermes` mentions with in-character replies

---

## File Structure

```
hermes-bot/
├── main.py                  # Bot entry point, command registration
├── config.py                # Tokens, API keys, channel IDs, settings
├── personality.py           # Hermes system prompt + LLM call wrapper
├── agent/
│   ├── hermes_agent.py      # Hermes LLM agent setup and tool routing
│   └── tools/
│       ├── steam_tools.py   # Steam API wrappers
│       ├── news_tools.py    # Game news fetcher
│       └── recap_tools.py   # Recap + power ranking generator
├── commands/
│   ├── steam_commands.py    # /link_steam, /unlink_steam, /common_games
│   ├── news_commands.py     # /game_news, manual triggers
│   └── recap_commands.py    # /weekly_recap, /power_rankings
├── tasks/
│   ├── news_watcher.py      # Scheduled news polling
│   └── recap_scheduler.py   # Weekly recap task
├── db/
│   ├── database.py          # SQLite setup and helpers
│   └── schema.sql           # DB schema
├── .env                     # Secrets (never commit)
├── requirements.txt
└── README.md
```

---

## Database Schema

```sql
-- Consenting users with Steam links
CREATE TABLE users (
    discord_id TEXT PRIMARY KEY,
    discord_name TEXT,
    steam_id TEXT,
    linked_at TIMESTAMP,
    opted_in BOOLEAN DEFAULT TRUE
);

-- Game libraries per user
CREATE TABLE user_games (
    discord_id TEXT,
    app_id INTEGER,
    game_name TEXT,
    playtime_minutes INTEGER,
    last_updated TIMESTAMP,
    PRIMARY KEY (discord_id, app_id)
);

-- Seen news items (dedup)
CREATE TABLE seen_news (
    app_id INTEGER,
    gid TEXT PRIMARY KEY,
    title TEXT,
    posted_at TIMESTAMP
);

-- Session logs (optional manual tracking)
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_name TEXT,
    players TEXT,  -- JSON array of discord_ids
    started_at TIMESTAMP,
    ended_at TIMESTAMP
);
```

---

## Hermes Personality System Prompt

```
You are Hermes, the divine messenger of the gaming realm. Your personality is 
a blend of a snarky sports commentator and a dramatic lore narrator from an 
ancient epic. You speak to your server members (the "mortals") with wit, 
occasional condescension, and theatrical flair.

Rules:
- Always stay in character. You are Hermes — swift, clever, and mildly 
  exasperated by mortals' gaming decisions.
- Address users as "mortals" or by their name.
- Treat game updates as divine proclamations from the developer gods.
- Frame wins triumphantly but with caveats. Frame losses as inevitable tragedy.
- Keep responses punchy. You are a herald, not a novelist.
- Never use generic AI phrases like "Certainly!" or "Great question!"
- When delivering news, open with a dramatic hook.
- Power rankings should feel like standings from an ancient colosseum.

Tone reference: Hermes from the game Hades — fast-talking, sardonic, 
enthusiastic about chaos, but ultimately rooting for the mortals.
```

---

## API Keys & Config Needed

| Key | Source | Used For |
|-----|--------|----------|
| `DISCORD_BOT_TOKEN` | Discord Developer Portal | Bot auth |
| `STEAM_API_KEY` | steamcommunity.com/dev/apikey | Library + news fetch |
| `HERMES_MODEL` / LLM config | Your Hermes agent setup | Personality responses |
| `NEWS_CHANNEL_ID` | Discord server | Where to post updates |
| `RECAP_CHANNEL_ID` | Discord server | Where to post recaps |

Store all in `.env`, load via `python-dotenv`.

---

## Dependencies

```
discord.py>=2.3.0
python-dotenv
aiohttp
aiosqlite
requests
apscheduler          # For scheduled tasks
# + your Hermes agent framework packages
```

---

## Build Order (Recommended)

Build in this sequence to keep things testable at each step:

1. **Bot skeleton** — connect to Discord, basic `/ping` command works
2. **Steam link flow** — `/link_steam`, fetch library, store in DB
3. **Common games** — `/common_games` command working
4. **Game news fetch** — pull Steam news for one game, post raw to channel
5. **Hermes personality layer** — pipe news through LLM, output in character
6. **News scheduler** — automate the news check
7. **Recap generator** — weekly recap with power rankings
8. **Ambient reactions** — Phase 2, add last

---

## Notes for the AI Assistant (Claude Code / OpenCode)

- Use `discord.py` with slash commands (`app_commands`)
- Use `aiosqlite` for async DB operations — this is an async bot
- Steam API for library: `GET https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/`
- Steam API for news: `GET https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/`
- The personality prompt lives in `personality.py` — all LLM calls should pass through there so the character stays consistent
- Hermes agent framework handles the actual LLM calls — wrap it so commands don't call the LLM directly, they call `personality.speak(context, data)`
- Keep the news dedup logic tight — nobody wants duplicate patch note announcements
- APScheduler works well with discord.py for background tasks
