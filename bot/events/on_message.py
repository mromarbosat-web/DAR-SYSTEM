import logging
import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.automod_service import AutoModService

logger = logging.getLogger("discord_bot.events.message")

def register_message_event(bot: commands.Bot):
    @bot.event
    async def on_message(message: discord.Message):
        if not message.guild or message.author.bot:
            return

        async with AsyncSessionLocal() as session:
            automod = AutoModService(session)
            flagged = await automod.process_message(message)
            if flagged:
                return # Message deleted & handled by AutoMod

        await bot.process_commands(message)
