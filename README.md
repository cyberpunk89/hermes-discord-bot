# Hermes — Discord Gaming Bot

A Discord bot powered by the [Hermes Agent Framework](https://hermes-agent.nousresearch.com), with the personality of Hermes from *Hades*. Built for a co-op gaming friend group — it tracks game prices, monitors Steam libraries, delivers patch notes, and generates dramatic weekly recaps.

> *"Another week passes in the mortal realm. Ninad led the charge in three sessions, yet somehow managed to die first in all of them. The prophecy remains... unclear."*

---

## Features

### Personality
Hermes speaks like a snarky sports commentator crossed with a dramatic lore narrator. Every response is in character — game updates are divine proclamations, price drops are acts of fate, losses are inevitable tragedy.

### Price Tracking
- Look up current retail and keyshop prices from GG.deals + IsThereAnyDeal
- Historical low prices and store comparisons
- Optional India (INR) pricing alongside EU prices
- Watchlist with alerts for price drops and target prices

### Steam Library Integration
- Link your Steam account to the group registry
- Find games everyone owns in common, sorted by collective playtime
- Automatic library refresh for weekly recaps

### Game News
- Monitors Steam news for all games in the group's common library
- Filters for patch notes, updates, hotfixes, and new content
- Deduplicates so nothing posts twice
- Delivered in character to `#game-news` every 4 hours

### Weekly Recaps
- Power rankings — who played most, who carried, who suffered
- Game of the Week based on collective hours
- Hermes' prophecy for the coming week
- Posts to `#recaps` every Sunday at 6 PM

---

## Commands

### Price

| Command | Description |
|---------|-------------|
| `/skill game-price <game>` | Get EU prices for a game by name or Steam URL |
| `/skill game-price <game> --india` | Include India (INR) prices alongside EU |

### Watchlist

| Command | Args | Description |
|---------|------|-------------|
| `/skill game-watchlist` | *(no args)* | Show available commands |
| `/skill game-watchlist` | `list` | View your watchlist with current prices |
| `/skill game-watchlist` | `add <game> [target €]` | Add a game, optionally with an alert price |
| `/skill game-watchlist` | `remove <game>` | Remove a game |
| `/skill game-watchlist` | `set-target <game> <price>` | Update the alert price for a game |
| `/skill game-watchlist` | `clear` | Remove all games from your watchlist |

### Steam Library

| Command | Args | Description |
|---------|------|-------------|
| `/skill steam-link` | `link <steam_id_or_vanity>` | Link your Steam account |
| `/skill steam-link` | `unlink` | Unlink your Steam account |
| `/skill steam-link` | `list-users` | See who's linked |

### Group Features

| Command | Description |
|---------|-------------|
| `/skill common-games` | Find games everyone owns in common |
| `/skill game-news` | Fetch latest game updates manually |
| `/skill weekly-recap` | Generate this week's power rankings |

---

## Setup

### Prerequisites
- [Hermes Agent](https://hermes-agent.nousresearch.com) installed
- Discord bot token with Message Content Intent enabled
- Steam Web API key — [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
- GG.deals API key (optional but recommended) — [gg.deals/api](https://gg.deals/api/)
- IsThereAnyDeal API key — [isthereanydeal.com/page/api](https://isthereanydeal.com/page/api/)

### Installation

```bash
git clone https://github.com/your-username/hermes-discord-bot
cd hermes-discord-bot
bash setup.sh
```

`setup.sh` will:
- Inject the install path into all skill scripts
- Create `.env` from `.env.example`
- Tell you what to add to `~/.hermes/config.yaml`

### Configuration

Edit `.env` in the project root (created by `setup.sh`):

```env
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_ALLOWED_USERS=your_discord_user_id
DISCORD_HOME_CHANNEL=your_main_channel_id

STEAM_API_KEY=your_steam_api_key
GG_DEALS_API_KEY=your_gg_deals_api_key
ITAD_API_KEY=your_itad_api_key

NEWS_CHANNEL_ID=your_game_news_channel_id
RECAP_CHANNEL_ID=your_recaps_channel_id
# DB_PATH defaults to watchlist.db in the project root — override if needed
```

Wire up the skills directory in `~/.hermes/config.yaml`:

```yaml
skills:
  external_dirs:
    - /path/to/hermes-discord-bot/skills
```

### Running

```bash
hermes gateway        # foreground (test)
hermes gateway run    # start as background service
```

The systemd service (`game-price-bot.service`) manages the background process:

```bash
sudo systemctl enable game-price-bot
sudo systemctl start game-price-bot
```

### Scheduled Tasks

Set these up once by telling Hermes in Discord:

```
/cron add "every 4h" "Fetch new game news for all tracked games and post to channel <NEWS_CHANNEL_ID> using the game-news skill" --skills game-news
/cron add "0 18 * * 0" "Generate and post the weekly recap and power rankings to channel <RECAP_CHANNEL_ID>" --skills weekly-recap
```

---

## Customising the Personality

Hermes' personality lives in a single file: **`~/.hermes/SOUL.md`**.

This file is injected as the system prompt for every conversation. Edit it to change how the bot speaks, what rules it follows, and how it frames different situations.

### What's in SOUL.md

```
~/.hermes/SOUL.md
```

The current prompt defines:
- **Identity** — Hermes, divine messenger, speaks in character at all times
- **Tone rules** — snarky sports commentator + dramatic lore narrator
- **Formatting rules** — punchy, no generic AI filler phrases
- **Voice examples** — concrete samples for price alerts, news, recaps

### How to Edit It

Open the file:

```bash
nano ~/.hermes/SOUL.md
# or
code ~/.hermes/SOUL.md
```

Changes take effect on the **next message** — no restart needed. The file is re-read per session.

### Common Tweaks

**Make responses shorter:**
```
- Keep responses to 1–3 sentences maximum. Be a herald, not a novelist.
```

**Change the persona entirely** — replace the Hermes framing with anything else:
```
You are Alfred, the dry-witted British butler of the gaming realm...
```

**Add a new tone rule:**
```
- When a game is on sale, always mention how many days the sale has left if known.
```

**Tune how it addresses users:**
```
- Address users by their first name only, never "mortal".
```

**Add server-specific context** (friends' names, running jokes, etc.):
```
## Group Context
- The group is: Ninad, Rohan, Priya, Dev
- Running joke: Ninad always picks the hardest difficulty and blames the game
- Rohan is the designated support main who claims he "doesn't need healing"
```

### Keeping a Backup

The `skills/` directory has no copy of SOUL.md — it lives only at `~/.hermes/SOUL.md`. Back it up before experimenting:

```bash
cp ~/.hermes/SOUL.md ~/.hermes/SOUL.md.bak
```

---

## Project Structure

```
hermes-bot/
├── skills/
│   ├── game-price/          # /skill game-price
│   │   ├── SKILL.md         # Instructions for the LLM
│   │   └── scripts/
│   │       └── price_lookup.py
│   ├── game-watchlist/      # /skill game-watchlist
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── watchlist_manager.py
│   ├── steam-link/          # /skill steam-link
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── steam_linker.py
│   ├── common-games/        # /skill common-games
│   ├── game-news/           # /skill game-news (+ cron)
│   └── weekly-recap/        # /skill weekly-recap (+ cron)
├── db/
│   └── database.py          # SQLite schema + all DB helpers
├── watchlist.db             # SQLite database (not in git)
├── game-price-bot.service   # Systemd unit file
└── hermes-bot-handoff.md    # Original design document
```

### How Skills Work

Each skill is a folder with two parts:

- **`SKILL.md`** — tells the LLM what to do, what commands to run, and how to interpret results. Edit this to change how a skill behaves.
- **`scripts/`** — the actual Python scripts the LLM calls via terminal. Edit these to change what data is fetched or stored.

The LLM reads `SKILL.md` when a skill is invoked, then runs the matching script and presents the output in character.

---

## Troubleshooting

**Bot not responding**
```bash
hermes gateway status
journalctl --user -u hermes-gateway.service -n 50
```

**Skills not showing as slash commands**
- Check `~/.hermes/config.yaml` has the correct `external_dirs` path
- Restart the gateway — it re-syncs slash commands on startup

**Bot creates a thread instead of replying inline**
- Ensure `~/.hermes/config.yaml` has a top-level `discord:` section (not nested under `platforms:`) with `auto_thread: false`:
  ```yaml
  discord:
    auto_thread: false
  ```

**Personality changes not taking effect**
- SOUL.md is re-read per session — changes apply to the next message, no restart needed
- If the bot seems stuck on old behaviour, send `/new` in Discord to start a fresh session

**Steam library not fetching**
- Ensure the Steam profile is set to public in Steam privacy settings
- Verify `STEAM_API_KEY` is set in `.env (in project root)`

**No price data**
- Verify `GG_DEALS_API_KEY` and `ITAD_API_KEY` in `.env (in project root)`
- GG.deals is the primary source; ITAD is the fallback

**Watchlist prices showing N/A**
- Prices are cached on add and refreshed on `list` if missing
- Run `/skill game-watchlist check-prices` to force a refresh for all entries

**Database issues**
- Confirm `DB_PATH` in `.env (in project root)` points to the correct `watchlist.db`
- Run `python3 db/database.py` to re-initialise tables

---

## License

MIT
