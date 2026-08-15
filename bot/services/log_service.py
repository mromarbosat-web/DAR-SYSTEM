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

    async def get_log_settings(self, guild_id: int):
        return await self.repo.get_log_settings(guild_id)

    async def update_log_settings(self, guild_id: int, **kwargs):
        logs = await self.repo.get_log_settings(guild_id)
        field_map = {
            "member_logs_channel_id": "member_log_channel_id",
            "message_logs_channel_id": "message_log_channel_id",
            "moderation_logs_channel_id": "moderation_log_channel_id",
            "role_logs_channel_id": "role_log_channel_id",
            "channel_logs_channel_id": "channel_log_channel_id",
            "server_logs_channel_id": "server_log_channel_id",
            "security_logs_channel_id": "security_log_channel_id",
            "voice_logs_channel_id": "voice_log_channel_id",
            "invite_logs_channel_id": "invite_log_channel_id",
            "economy_logs_channel_id": "economy_log_channel_id",
            "verification_logs_channel_id": "verification_log_channel_id",
            "automod_logs_channel_id": "automod_log_channel_id",
        }
        for k, v in kwargs.items():
            db_field = field_map.get(k, k)
            if hasattr(logs, db_field):
                setattr(logs, db_field, v)
        await self.session.commit()
        await self.session.refresh(logs)
        return logs

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
