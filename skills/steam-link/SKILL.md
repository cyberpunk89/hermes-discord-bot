---
name: steam-link
description: Link or unlink a mortal's Steam account, or list all linked users. Use when someone wants to connect their Steam library to the group.
version: 1.0.0
author: your-username
---

# Steam Account Linking

## MANDATORY — DO NOT SKIP

**YOU MUST RUN THE SCRIPT FIRST. This is not optional.**

1. Run the terminal command BEFORE responding
2. The script output MUST appear in your response
3. DO NOT make up data — use ONLY script output
4. If the script fails, state the error clearly
5. If the script output is empty or unexpected, re-run it — don't guess

**Failure to run the script will result in incorrect responses.**

## IMPORTANT
Run the terminal command immediately. Do not simulate the result. Do not print or echo the terminal command in your response. Never search for discord_id. Never ask the user for their discord_id.

The user's display name is available in the message context. In a multi-user Discord channel, each message is prefixed `[Name]: message` — extract the name from that prefix and pass it as `<display_name>`. In a DM, use the `**User:**` field from the system prompt. Never pass an empty string.

The `<steam_id_or_vanity>` MUST be taken verbatim from the user's message — the number or slug they explicitly provided. NEVER use the display name as the steam input. NEVER infer or guess the steam ID from the user's name.

## Commands

**Link a Steam account** (steam_id can be a 64-bit ID or vanity URL slug):
```
python3 /home/nikel/Documents/projects/discord/game-price-bot/skills/steam-link/scripts/steam_linker.py link "<display_name>" "<steam_id_or_vanity>"
```

Pass exactly 2 arguments after `link`: the display name, then the Steam ID/vanity. Do NOT pass a discord_id as a third or first argument.

**Unlink:**
```
python3 /home/nikel/Documents/projects/discord/game-price-bot/skills/steam-link/scripts/steam_linker.py unlink "<display_name>"
```

**List linked users:**
```
python3 /home/nikel/Documents/projects/discord/game-price-bot/skills/steam-link/scripts/steam_linker.py list-users
```

## Output Interpretation
- `LINKED: <name>` + `GAME_COUNT: <n>` — success
- `VANITY_NOT_FOUND` — ask for numeric SteamID64 instead
- `LIBRARY_PRIVATE_OR_ERROR` — library is private on Steam
- `UNLINKED` — removed successfully
- `ERROR: Unknown user` — display_name was empty; check message context

## Response Style
Linking = joining the divine registry. Unlinking = departing the sacred scrolls.
