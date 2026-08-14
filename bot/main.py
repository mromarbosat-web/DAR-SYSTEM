import asyncio
import logging
import sys
import discord
from discord.ext import commands
from bot.config.settings import settings
from bot.database.connection import init_db
from bot.utils.logger import logger
from bot.utils.invite_tracker import setup_invite_tracker
from bot.database.migrations.migration_manager import run_migrations
from bot.events.on_ready import register_ready_event
from bot.events.on_member_join import register_member_join_event
from bot.events.on_member_remove import register_member_remove_event
from bot.events.on_message import register_message_event
from bot.events.on_message_events import register_message_logs_events
from bot.events.on_voice_events import register_voice_logs_events
from bot.events.on_role_events import register_role_logs_events
from bot.events.on_channel_events import register_channel_logs_events
from bot.events.on_server_events import register_server_logs_events
from bot.events.on_member_events_ext import register_member_logs_ext_events

from bot.events.on_audit_log import register_audit_log_event
from bot.events.error_handler import register_error_handlers

# Configure Discord Intents
intents = discord.Intents.default()
intents.members = True          # Required for Anti-Raid, Verification, Logs
intents.message_content = True  # Required for AutoMod & Anti-Spam
intents.guilds = True           # Required for Server & Channel management
intents.moderation = True       # Required for Audit Logs & Anti-Nuke
intents.voice_states = True     # Required for Voice Logs
intents.invites = True          # Required for Invite Tracking

class SecurityBot(commands.Bot):
    def __init__(self):
        super().__init__(
            max_messages=10000, # Large message cache for Message Delete Logs
            command_prefix=settings.DEFAULT_PREFIX,
            intents=intents,
            help_command=None
        )
        self.invite_tracker = setup_invite_tracker(self)

    async def setup_hook(self):
        logger.info("Initializing database schema...")
        await init_db()
        
        logger.info("Running database migrations...")
        await run_migrations()

        # Load Cogs
        initial_extensions = [
            "bot.cogs.security",
            "bot.cogs.automod",
            "bot.cogs.moderation",
            "bot.cogs.warnings",
            "bot.cogs.voice",
            "bot.cogs.verification",
            "bot.cogs.logs",
            "bot.cogs.whitelist",
            "bot.cogs.setup",
            "bot.cogs.utility",
            "bot.cogs.permissions",
            "bot.cogs.role_management",
            "bot.cogs.economy",
            "bot.cogs.shop",
            "bot.cogs.profile",
            "bot.cogs.leaderboard",
            "bot.cogs.shortcuts",
            "bot.cogs.help",
            "bot.cogs.control"
        ]

        for ext in initial_extensions:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded cog extension: {ext}")
            except Exception as e:
                logger.critical(f"CRITICAL: Failed to load {ext}: {e}", exc_info=True)
                raise RuntimeError(f"CRITICAL: Failed to load cog extension {ext}") from e

async def main():
    if not settings.DISCORD_BOT_TOKEN:
        logger.warning(
            "DISCORD_BOT_TOKEN is missing in environment variables! "
            "Please provide a valid token in Railway / .env before starting in production."
        )

    bot = SecurityBot()

    # Register Event Listeners
    register_ready_event(bot)
    register_member_join_event(bot)
    register_member_remove_event(bot)
    register_message_event(bot)
    register_message_logs_events(bot)
    register_voice_logs_events(bot)
    register_role_logs_events(bot)
    register_channel_logs_events(bot)
    register_server_logs_events(bot)
    register_member_logs_ext_events(bot)

    register_audit_log_event(bot)
    register_error_handlers(bot)

    if settings.DISCORD_BOT_TOKEN:
        try:
            logger.info("Starting Security & Management Discord Bot...")
            await bot.start(settings.DISCORD_BOT_TOKEN)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received.")
            await bot.close()
        except Exception as e:
            logger.critical(f"Fatal error during bot execution: {e}", exc_info=True)
    else:
        logger.info("Bot execution paused because DISCORD_BOT_TOKEN is empty.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
        sys.exit(0)
