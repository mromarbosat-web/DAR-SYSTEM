from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import LogSettings, GuildRepository

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
            result = await self.session.execute(stmt)
            settings = result.scalar_one_or_none()
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
            "security": "security_log_channel_id"
        }
        if log_type in field_map:
            setattr(logs, field_map[log_type], channel_id)
            await self.session.commit()
            await self.session.refresh(logs)
        return logs
