---
name: should-buy
description: "Verdict on whether the group should buy a game — checks who owns it, current price, co-op status, and total cost for those who don't have it yet."
version: 1.0.0
author: your-username
---

# Should We Buy This?

## IMPORTANT
Run the terminal command immediately. Do not guess prices or ownership. Do not print or echo the terminal command in your response.

Extract member names from the user's message. If they mention specific people ("me and Nikel", "for Nikel and furaiboi"), pass those names as separate arguments. If no members are mentioned, omit them — the script will check all linked users.

## Command

```
python3 <INSTALL_DIR>/skills/should-buy/scripts/should_buy.py "<game name>" [member1] [member2] ...
```

Examples:
```
python3 <INSTALL_DIR>/skills/should-buy/scripts/should_buy.py "Elden Ring"
python3 <INSTALL_DIR>/skills/should-buy/scripts/should_buy.py "Deep Rock Galactic" "Nikel" "furaiboi"
```

## Output Interpretation

- `NOT_FOUND` — game not found on Steam; ask for a different name
- `GAME: <name>` — resolved game title
- `COOP: Yes | MODES: <modes>` or `COOP: No`
- `CURRENT_PRICE: €<n>` — best current retail price
- `HISTORICAL_LOW: €<n>` — all-time low
- `PRICE_STATUS: AT_OR_NEAR_HISTORICAL_LOW` — great time to buy
- `PRICE_STATUS: <n>% ABOVE HISTORICAL LOW` — how far from the best price ever
- `OWNS: <name>` — this member already owns it
- `NEEDS_TO_BUY: <name> | COST: €<n>` — one line per member who doesn't own it
- `TOTAL_COST: €<n> for <n> member(s)` — combined spend

## Response Style

Give a **divine verdict** — is it worth it or should they wait?

Structure:
1. What the game is + co-op status (one punchy line)
2. Who owns it vs who needs to buy
3. Price situation — if near historical low, urge them to act now; if far above, suggest patience
4. Total cost for the group
5. The verdict: "Buy now", "Wait for a sale", or "One of you can share" if someone owns it

Frame it like Hermes delivering a prophecy: decisive, dramatic, never wishy-washy.

Always wrap every URL in angle brackets to suppress Discord embed previews: `<https://example.com>`. Never paste bare URLs.
