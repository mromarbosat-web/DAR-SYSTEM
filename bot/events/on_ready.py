import logging
import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.verification_service import VerificationView

logger = logging.getLogger("discord_bot.events.ready")

def register_ready_event(bot: commands.Bot):
    @bot.event
    async def on_ready():
        logger.info(f"Bot logged in successfully as {bot.user} (ID: {bot.user.id})")
        logger.info(f"Connected to {len(bot.guilds)} Discord guilds.")

        # Reconnect guard: Only sync slash commands and register views on first ready
        if not getattr(bot, "_has_initialized_on_ready", False):
            bot._has_initialized_on_ready = True

            # Register persistent Verification Button View
            try:
                bot.add_view(VerificationView(AsyncSessionLocal))
                logger.info("Persistent Verification Button View registered.")
            except Exception as e:
                logger.error(f"Error registering Verification persistent view: {e}")

            # Sync Slash Commands with Discord Gateway
            try:
                synced = await bot.tree.sync()
                logger.info(f"Successfully synced {len(synced)} application slash commands globally.")
            except Exception as e:
                logger.error(f"Error syncing application slash commands: {e}")

        # Set Activity Status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Shielding Servers • /security"
        )
        await bot.change_presence(activity=activity, status=discord.Status.online)
