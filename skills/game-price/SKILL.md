---
name: game-price
description: "Look up game prices (EU + optionally India) — price <game> [india]"
version: 1.0.0
author: your-username
---

# Game Price Lookup

## IMPORTANT
You MUST run the terminal command to get real price data. Never make up prices or respond without running the script first. Do not ask the mortal to "whisper" anything — just run the script. Do not print or echo the terminal command in your response.

## Steps

1. If the mortal has not provided a game name or URL, ask for it once — briefly.
2. As soon as you have a game name or URL, run this command immediately:

```
python3 <INSTALL_DIR>/skills/game-price/scripts/price_lookup.py "<game name or steam url>"
```

To include India (INR) prices, append `--india`:
```
python3 <INSTALL_DIR>/skills/game-price/scripts/price_lookup.py "<game name or steam url>" --india
```

3. Read the output and present the results. Do not skip the terminal call.

## Output Fields

- `TITLE` — game name
- `CURRENT_RETAIL` — best retail store price in EUR
- `CURRENT_KEYSHOP` — best keyshop price in EUR  
- `HIST_RETAIL` — all-time lowest retail price
- `HIST_KEYSHOP` — all-time lowest keyshop price
- `CURRENT_RETAIL_IN` — best retail price in INR (only with `--india`)
- `HIST_RETAIL_IN` — all-time lowest retail price in INR (only with `--india`)
- `STORE_URL` — Steam store link
- `GG_DEALS_URL` — GG.deals comparison link
- `METACRITIC` — critic score

If output is `NO_RESULT`, the game wasn't found — ask for a different name.

## Response Style
Present results in Hermes character. Include the store links. Frame deals dramatically:
- Great deal → "The fates smile upon you, mortal..."
- Expensive → "The developer gods demand a steep toll..."
- Historical low → "A once-in-an-epoch price. Act swiftly."

Always wrap every URL in angle brackets to suppress Discord embed previews: `<https://store.steampowered.com/app/123/>`. Never paste bare URLs.
