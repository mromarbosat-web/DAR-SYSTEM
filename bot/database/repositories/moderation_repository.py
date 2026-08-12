from typing import List, Optional
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import Warning, ModerationAction, PunishmentSettings, GuildRepository

class ModerationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_punishment_settings(self, guild_id: int) -> PunishmentSettings:
        stmt = select(PunishmentSettings).where(PunishmentSettings.guild_id == guild_id)
        result = await self.session.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            guild_repo = GuildRepository(self.session)
            await guild_repo.get_or_create_guild(guild_id, f"Guild_{guild_id}")
            result = await self.session.execute(stmt)
            settings = result.scalar_one_or_none()
        return settings

    async def update_punishment_settings(self, guild_id: int, **kwargs) -> PunishmentSettings:
        settings = await self.get_punishment_settings(guild_id)
        for key, value in kwargs.items():
            if hasattr(settings, key) and value is not None:
                setattr(settings, key, value)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> Warning:
        # Ensure guild exists
        guild_repo = GuildRepository(self.session)
        await guild_repo.get_or_create_guild(guild_id, f"Guild_{guild_id}")
        
        warning = Warning(
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            reason=reason
        )
        self.session.add(warning)
        await self.session.commit()
        await self.session.refresh(warning)
        return warning

    async def get_user_warnings(self, guild_id: int, user_id: int) -> List[Warning]:
        stmt = select(Warning).where(
            Warning.guild_id == guild_id,
            Warning.user_id == user_id
        ).order_by(Warning.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_warning_count(self, guild_id: int, user_id: int) -> int:
        stmt = select(func.count(Warning.warning_id)).where(
            Warning.guild_id == guild_id,
            Warning.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def remove_warning(self, guild_id: int, warning_id: str) -> bool:
        stmt = delete(Warning).where(
            Warning.guild_id == guild_id,
            Warning.warning_id == warning_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def log_moderation_action(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        action_type: str,
        reason: Optional[str] = None,
        duration: Optional[int] = None
    ) -> ModerationAction:
        action = ModerationAction(
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            action_type=action_type,
            reason=reason,
            duration=duration
        )
        self.session.add(action)
        await self.session.commit()
        await self.session.refresh(action)
        return action
