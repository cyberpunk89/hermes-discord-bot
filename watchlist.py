import os
import discord
from discord import app_commands
from discord.ext import tasks
import asyncio
import datetime
from tools import search_game, get_game_info
from database import (
    add_to_watchlist,
    remove_from_watchlist,
    get_user_watchlist,
    get_all_watchlist,
    update_last_prices,
    set_target_price,
    toggle_notification,
    count_user_watchlist,
    clear_user_watchlist,
    find_by_game_title,
)

MAX_WATCHLIST = 20
GG_KEY = None
ITAD_KEY = None


def setup_watchlist(bot: discord.Client, tree: app_commands.CommandTree, gg_key: str, itad_key: str):
    global GG_KEY, ITAD_KEY
    GG_KEY = gg_key
    ITAD_KEY = itad_key

    watchlist_group = app_commands.Group(name="watchlist", description="Manage your game watchlist")

    @watchlist_group.command(name="add", description="Add a game to your watchlist")
    async def add_cmd(
        interaction: discord.Interaction,
        game: str,
        target_price: float = None,
    ):
        await interaction.response.defer()

        user_id = str(interaction.user.id)
        user_name = str(interaction.user)

        if count_user_watchlist(user_id) >= MAX_WATCHLIST:
            await interaction.followup.send(
                f"⚠️ You have reached the maximum of {MAX_WATCHLIST} games in your watchlist. "
                "Remove some games to add more."
            )
            return

        info = search_game(game, GG_KEY, ITAD_KEY if ITAD_KEY else None)
        if not info:
            await interaction.followup.send(f"❌ Couldn't find game: {game}")
            return

        success = add_to_watchlist(
            user_id=user_id,
            user_name=user_name,
            appid=info["appid"],
            game_title=info["title"],
            target_price=target_price,
            notify_any_drop=True,
            notify_hist_low=True,
        )

        if success:
            embed = discord.Embed(
                title=f"✅ Added to Watchlist",
                description=info["title"],
                color=0x00FF00,
            )
            if target_price:
                embed.add_field(name="Target Price", value=f"€{target_price}", inline=True)
            embed.add_field(name="Current Price", value=f"€{info.get('current_retail', 'N/A')}", inline=True)
            embed.add_field(name="Notifications", value="📉 Any drop: ON\n🏆 Hist. Low: ON", inline=False)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("⚠️ This game is already in your watchlist!")

    @watchlist_group.command(name="remove", description="Remove a game from your watchlist")
    async def remove_cmd(interaction: discord.Interaction, game: str):
        await interaction.response.defer()

        user_id = str(interaction.user.id)
        entry = find_by_game_title(user_id, game)

        if not entry:
            await interaction.followup.send(f"❌ Game not found in your watchlist: {game}")
            return

        success = remove_from_watchlist(user_id, entry["appid"])
        if success:
            await interaction.followup.send(f"✅ Removed '{entry['game_title']}' from watchlist")
        else:
            await interaction.followup.send("❌ Failed to remove game")

    @watchlist_group.command(name="list", description="Show your watchlist")
    async def list_cmd(interaction: discord.Interaction):
        await interaction.response.defer()

        user_id = str(interaction.user.id)
        watchlist = get_user_watchlist(user_id)

        if not watchlist:
            await interaction.followup.send("📭 Your watchlist is empty!")
            return

        embed = discord.Embed(
            title=f"🎮 {interaction.user.display_name}'s Watchlist",
            color=0x1B2838,
        )

        for item in watchlist[:10]:
            title = item["game_title"]
            current = item["last_retail_price"]
            target = item["target_price"]
            any_drop = "📉" if item["notify_any_drop"] else "📭"
            hist_low = "🏆" if item["notify_hist_low"] else "🏳️"

            price_str = f"€{current:.2f}" if current else "N/A"
            target_str = f" → €{target:.2f}" if target else ""
            status = f"{any_drop} {hist_low}"

            embed.add_field(
                name=title,
                value=f"{price_str}{target_str}\n{status}",
                inline=True,
            )

        total = len(watchlist)
        embed.set_footer(text=f"Showing 10 of {total} games. Use /watchlist for full list.")

        await interaction.followup.send(embed=embed)

    @watchlist_group.command(name="set-target", description="Set target price for a game")
    async def set_target_cmd(
        interaction: discord.Interaction,
        game: str,
        target_price: float,
    ):
        await interaction.response.defer()

        user_id = str(interaction.user.id)
        entry = find_by_game_title(user_id, game)

        if not entry:
            await interaction.followup.send(f"❌ Game not found in your watchlist: {game}")
            return

        set_target_price(user_id, entry["appid"], target_price)
        await interaction.followup.send(
            f"✅ Set target price for '{entry['game_title']}' to €{target_price:.2f}"
        )

    @watchlist_group.command(name="toggle", description="Toggle notification settings")
    async def toggle_cmd(
        interaction: discord.Interaction,
        game: str,
        notification_type: str,
        enabled: bool,
    ):
        await interaction.response.defer()

        user_id = str(interaction.user.id)
        entry = find_by_game_title(user_id, game)

        if not entry:
            await interaction.followup.send(f"❌ Game not found in your watchlist: {game}")
            return

        if notification_type not in ["any-drop", "hist-low"]:
            await interaction.followup.send(
                "⚠️ Invalid type. Use 'any-drop' or 'hist-low'"
            )
            return

        notif_type = "any_drop" if notification_type == "any-drop" else "hist_low"
        success = toggle_notification(user_id, entry["appid"], notif_type, enabled)

        if success:
            status = "enabled" if enabled else "disabled"
            await interaction.followup.send(
                f"✅ {notification_type} notifications {status} for '{entry['game_title']}'"
            )
        else:
            await interaction.followup.send("❌ Failed to update settings")

    @watchlist_group.command(name="clear", description="Clear your entire watchlist")
    async def clear_cmd(interaction: discord.Interaction):
        await interaction.response.defer()

        user_id = str(interaction.user.id)
        count = clear_user_watchlist(user_id)

        await interaction.followup.send(f"✅ Cleared {count} games from your watchlist")

    tree.add_command(watchlist_group)

    run_time = datetime.time(hour=9, minute=0, tzinfo=datetime.timezone.utc)

    @tasks.loop(time=run_time)
    async def check_prices():
        await asyncio.sleep(5)
        print("🔄 Running daily price check...")

        watchlist = get_all_watchlist()
        if not watchlist:
            print("No games in watchlist")
            return

        processed = set()
        for item in watchlist:
            appid = item["appid"]
            if appid in processed:
                continue
            processed.add(appid)

            try:
                info = get_game_info(appid, GG_KEY, ITAD_KEY if ITAD_KEY else None)
                if not info:
                    continue

                current_retail = info.get("current_retail")
                current_keyshop = info.get("current_keyshops")

                update_last_prices(appid, current_retail, current_keyshop)

                notify_any = item["notify_any_drop"]
                notify_hist = item["notify_hist_low"]
                target = item["target_price"]
                last_price = item["last_retail_price"]

                alerts = []

                if target and current_retail and current_retail <= target:
                    alerts.append(f"🎯 Target price reached! €{current_retail} <= €{target}")

                if notify_any and last_price and current_retail:
                    drop_pct = ((last_price - current_retail) / last_price) * 100
                    if drop_pct >= 10:
                        alerts.append(f"📉 Price dropped {drop_pct:.0f}%! (€{last_price} → €{current_retail})")

                if notify_hist and current_retail and info.get("historical_retail"):
                    if current_retail <= info["historical_retail"]:
                        alerts.append(f"🏆 Historical low! €{current_retail}")

                if alerts:
                    user = bot.get_user(int(item["user_id"]))
                    if user:
                        embed = discord.Embed(
                            title=f"🔔 Price Alert: {info['title']}",
                            url=info["store_url"],
                            color=0xFF0000 if "low" in str(alerts).lower() else 0xFFA500,
                        )
                        for alert in alerts:
                            embed.add_field(name="Alert", value=alert, inline=False)

                        if info.get("image"):
                            embed.set_thumbnail(url=info["image"])

                        embed.add_field(
                            name="Current Prices",
                            value=f"Retail: €{current_retail}\nKeyshop: €{current_keyshop or 'N/A'}",
                            inline=True,
                        )
                        embed.add_field(
                            name="History",
                            value=f"Low: €{info.get('historical_retail', 'N/A')}",
                            inline=True,
                        )

                        try:
                            await user.send(embed=embed)
                            print(f"📧 Notified {item['user_name']} about {info['title']}")
                        except Exception as e:
                            print(f"⚠️ Failed to DM {item['user_id']}: {e}")

            except Exception as e:
                print(f"Error checking {appid}: {e}")
                await asyncio.sleep(1)

        print("✅ Price check complete")

    @check_prices.before_loop
    async def before_check():
        await bot.wait_until_ready()

    try:
        check_prices.start()
        print("✅ Watchlist scheduler started")
    except Exception as e:
        print(f"⚠️ Scheduler failed to start: {e}")
        print("Watchlist commands still functional without auto-check")