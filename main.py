import os
import discord
from discord import app_commands
from dotenv import load_dotenv
from tools import detect_steam_link, is_search_query, get_game_info, search_game
from watchlist import setup_watchlist

load_dotenv()

TOKEN = os.environ["DISCORD_TOKEN"]
GG_DEALS_KEY = os.environ.get("GG_DEALS_API_KEY", "")
ITAD_KEY = os.environ.get("ITAD_API_KEY", "")

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Setting up watchlist...")
    setup_watchlist(bot, tree, GG_DEALS_KEY, ITAD_KEY if ITAD_KEY else None)
    print("Watchlist setup complete, syncing commands...")
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} commands: {[c.name for c in synced]}")
    except Exception as e:
        print(f"Sync error: {e}")


@tree.command(name="price", description="Get game price from Steam URL or name")
async def price_command(interaction: discord.Interaction, query: str):
    await interaction.response.defer()

    appid = detect_steam_link(query)
    is_search = is_search_query(query)

    if is_search:
        info = search_game(query, GG_DEALS_KEY, ITAD_KEY if ITAD_KEY else None)
    elif appid:
        info = get_game_info(appid, GG_DEALS_KEY, ITAD_KEY if ITAD_KEY else None)
    else:
        await interaction.followup.send("Couldn't recognize that. Use a Steam URL or game name.")
        return

    if not info:
        await interaction.followup.send("Couldn't find game info. Check the name or try again.")
        return

    embed = _build_embed(info)
    await interaction.followup.send(embed=embed)


@tree.command(name="game", description="Search for a game by name")
async def game_command(interaction: discord.Interaction, name: str):
    await interaction.response.defer()

    info = search_game(name, GG_DEALS_KEY, ITAD_KEY if ITAD_KEY else None)

    if not info:
        await interaction.followup.send(f"Couldn't find '{name}'. Try a different name.")
        return

    embed = _build_embed(info)
    await interaction.followup.send(embed=embed)


def _build_embed(info: dict) -> discord.Embed:
    currency = info.get("currency", "EUR")
    symbol = "€" if currency == "EUR" else "$" if currency == "USD" else currency

    embed = discord.Embed(
        title=info["title"] or "Unknown Game",
        url=info["store_url"],
        color=0x1B2838,
    )

    if info["image"]:
        embed.set_thumbnail(url=info["image"])

    retail = info.get("current_retail")
    store = info.get("current_retail_store")
    retail_url = info.get("current_retail_url")
    keyshop = info.get("current_keyshops")

    if retail and retail_url:
        store_str = f" @ {store}" if store else ""
        embed.add_field(
            name="🏷️ Best Price (Retail)",
            value=f"[{symbol}{retail}{store_str}]({retail_url})",
            inline=False,
        )

    if keyshop:
        embed.add_field(name="🔑 Best Price (Keyshop)", value=f"{symbol}{keyshop}", inline=False)
    elif not retail:
        embed.add_field(name="🏷️ Best Price", value="No deals found", inline=False)

    hist_retail = info.get("historical_retail")
    hist_keyshop = info.get("historical_keyshops")

    if hist_retail and hist_keyshop:
        embed.add_field(
            name="📉 Historical Low",
            value=f"Retail: {symbol}{hist_retail} | Keyshop: {symbol}{hist_keyshop}",
            inline=True,
        )
    elif hist_retail:
        embed.add_field(
            name="📉 Historical Low (Retail)",
            value=f"{symbol}{hist_retail}",
            inline=True,
        )
    elif hist_keyshop:
        embed.add_field(
            name="📉 Historical Low (Keyshop)",
            value=f"{symbol}{hist_keyshop}",
            inline=True,
        )
    else:
        embed.add_field(name="📉 Historical Low", value="N/A", inline=True)

    if info["release_date"]:
        embed.add_field(name="📅 Release Date", value=info["release_date"], inline=True)

    if info["platforms"]:
        embed.add_field(name="🖥️ Platforms", value=info["platforms"], inline=True)

    if info["developer"]:
        embed.add_field(name="👨‍💻 Developer", value=info["developer"], inline=True)

    if info["publisher"]:
        embed.add_field(name="🏢 Publisher", value=info["publisher"], inline=True)

    if info["genres"]:
        embed.add_field(name="🎮 Genres", value=info["genres"], inline=True)

    if info["metacritic"] is not None:
        embed.add_field(name="⭐ Metacritic", value=str(info["metacritic"]), inline=True)

    if info["steam_rating"]:
        rating = info["steam_rating"].get("rating")
        reviews = info["steam_reviews"]
        if rating and reviews:
            embed.add_field(
                name="📕 Steam Reviews",
                value=f"{rating} ({reviews} reviews)",
                inline=True,
            )

    if info["deals"]:
        top_deals = _format_top_deals(info["deals"][:5], symbol)
        if top_deals:
            embed.add_field(name="🏪 Top Stores", value=top_deals, inline=False)

    if info["gg_deals_url"]:
        embed.add_field(name="🔗 GG.deals", value=f"[Link]({info['gg_deals_url']})", inline=False)

    embed.set_footer(text="Data via GG.deals + Steam")
    return embed


def _format_top_deals(deals: list, symbol: str) -> str:
    lines = []
    for deal in deals:
        shop_name = deal.get("shop", {}).get("name", "Unknown")
        price = deal.get("price", {}).get("amount")
        url = deal.get("url", "")
        if price:
            lines.append(f"[{symbol}{price} @ {shop_name}]({url})")
    return "\n".join(lines[:5]) if lines else ""


bot.run(TOKEN)