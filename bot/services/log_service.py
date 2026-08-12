import logging
import discord
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.repositories.log_repository import LogRepository
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.log_service")

class LogService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = LogRepository(session)

    async def log_event(
        self,
        guild: discord.Guild,
        log_type: str, # member, message, moderation, role, channel, server, security
        embed: discord.Embed
    ):
        """Sends an event log embed to the configured channel for the log_type"""
        try:
            settings = await self.repo.get_log_settings(guild.id)
            if not settings:
                return

            channel_id_attr = f"{log_type}_log_channel_id"
            channel_id = getattr(settings, channel_id_attr, None)

            if channel_id:
                channel = guild.get_channel(channel_id)
                if channel and isinstance(channel, discord.TextChannel):
                    await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error logging event {log_type} in guild {guild.id}: {e}")
