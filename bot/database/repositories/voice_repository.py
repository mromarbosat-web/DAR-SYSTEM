from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import VoiceSettings, VoiceActionLog
from bot.database.repositories.guild_repository import GuildRepository

class VoiceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_voice_settings(self, guild_id: int) -> VoiceSettings:
        stmt = select(VoiceSettings).where(VoiceSettings.guild_id == guild_id)
        result = await self.session.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            guild_repo = GuildRepository(self.session)
            await guild_repo.get_or_create_guild(guild_id, f"Guild_{guild_id}")
            settings = VoiceSettings(guild_id=guild_id)
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)
        return settings

    async def update_voice_settings(self, guild_id: int, **kwargs) -> VoiceSettings:
        settings = await self.get_or_create_voice_settings(guild_id)
        for key, value in kwargs.items():
            if hasattr(settings, key) and value is not None:
                setattr(settings, key, value)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    async def log_voice_action(
        self,
        guild_id: int,
        executor_id: int,
        action_type: str,
        target_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        target_channel_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> VoiceActionLog:
        guild_repo = GuildRepository(self.session)
        await guild_repo.get_or_create_guild(guild_id, f"Guild_{guild_id}")

        log = VoiceActionLog(
            guild_id=guild_id,
            executor_id=executor_id,
            target_id=target_id,
            action_type=action_type,
            channel_id=channel_id,
            target_channel_id=target_channel_id,
            reason=reason
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_voice_logs(self, guild_id: int, limit: int = 50) -> List[VoiceActionLog]:
        stmt = (
            select(VoiceActionLog)
            .where(VoiceActionLog.guild_id == guild_id)
            .order_by(VoiceActionLog.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
