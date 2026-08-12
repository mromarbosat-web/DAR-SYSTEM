from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import LogSettings
from bot.database.repositories.guild_repository import GuildRepository

class LogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_log_settings(self, guild_id: int) -> LogSettings:
        stmt = select(LogSettings).where(LogSettings.guild_id == guild_id)
        result = await self.session.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            guild_repo = GuildRepository(self.session)
            await guild_repo.get_or_create_guild(guild_id, f"Guild_{guild_id}")
            settings = LogSettings(guild_id=guild_id)
            self.session.add(settings)
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()
            await self.session.refresh(settings)
        return settings

    async def update_log_channel(self, guild_id: int, log_type: str, channel_id: Optional[int]) -> LogSettings:
        logs = await self.get_log_settings(guild_id)
        field_map = {
            "member": "member_log_channel_id",
            "message": "message_log_channel_id",
            "moderation": "moderation_log_channel_id",
            "role": "role_log_channel_id",
            "channel": "channel_log_channel_id",
            "server": "server_log_channel_id",
            "security": "security_log_channel_id",
            "voice": "voice_log_channel_id",
            "invite": "invite_log_channel_id",
            "economy": "economy_log_channel_id",
            "verification": "verification_log_channel_id",
            "automod": "automod_log_channel_id"
        }
        if log_type in field_map:
            setattr(logs, field_map[log_type], channel_id)
            await self.session.commit()
            await self.session.refresh(logs)
        return logs
