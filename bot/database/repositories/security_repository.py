from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import SecuritySettings, GuildRepository

class SecurityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_security_settings(self, guild_id: int) -> SecuritySettings:
        stmt = select(SecuritySettings).where(SecuritySettings.guild_id == guild_id)
        result = await self.session.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            # Ensure guild exists first
            guild_repo = GuildRepository(self.session)
            await guild_repo.get_or_create_guild(guild_id, f"Guild_{guild_id}")
            result = await self.session.execute(stmt)
            settings = result.scalar_one_or_none()
        return settings

    async def update_anti_raid(
        self,
        guild_id: int,
        enabled: Optional[bool] = None,
        threshold: Optional[int] = None,
        window: Optional[int] = None,
        action: Optional[str] = None
    ) -> SecuritySettings:
        sec = await self.get_security_settings(guild_id)
        if enabled is not None:
            sec.anti_raid_enabled = enabled
        if threshold is not None:
            sec.anti_raid_join_threshold = threshold
        if window is not None:
            sec.anti_raid_time_window = window
        if action is not None:
            sec.anti_raid_action = action
        await self.session.commit()
        await self.session.refresh(sec)
        return sec

    async def update_anti_nuke(
        self,
        guild_id: int,
        enabled: Optional[bool] = None,
        channel_threshold: Optional[int] = None,
        role_threshold: Optional[int] = None,
        window: Optional[int] = None,
        action: Optional[str] = None
    ) -> SecuritySettings:
        sec = await self.get_security_settings(guild_id)
        if enabled is not None:
            sec.anti_nuke_enabled = enabled
        if channel_threshold is not None:
            sec.anti_nuke_channel_threshold = channel_threshold
        if role_threshold is not None:
            sec.anti_nuke_role_threshold = role_threshold
        if window is not None:
            sec.anti_nuke_time_window = window
        if action is not None:
            sec.anti_nuke_action = action
        await self.session.commit()
        await self.session.refresh(sec)
        return sec
