from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import AutoModSettings
from bot.database.repositories.guild_repository import GuildRepository

class AutoModRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_automod_settings(self, guild_id: int) -> AutoModSettings:
        stmt = select(AutoModSettings).where(AutoModSettings.guild_id == guild_id)
        result = await self.session.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            guild_repo = GuildRepository(self.session)
            await guild_repo.get_or_create_guild(guild_id, f"Guild_{guild_id}")
            settings = AutoModSettings(guild_id=guild_id)
            self.session.add(settings)
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()
            await self.session.refresh(settings)
        return settings

    async def update_automod_settings(self, guild_id: int, **kwargs) -> AutoModSettings:
        automod = await self.get_automod_settings(guild_id)
        for key, value in kwargs.items():
            if hasattr(automod, key) and value is not None:
                setattr(automod, key, value)
        await self.session.commit()
        await self.session.refresh(automod)
        return automod

    async def add_bad_words(self, guild_id: int, words: List[str]) -> AutoModSettings:
        automod = await self.get_automod_settings(guild_id)
        current = set(automod.bad_words or [])
        current.update(w.lower().strip() for w in words if w.strip())
        automod.bad_words = list(current)
        await self.session.commit()
        await self.session.refresh(automod)
        return automod

    async def remove_bad_words(self, guild_id: int, words: List[str]) -> AutoModSettings:
        automod = await self.get_automod_settings(guild_id)
        current = set(automod.bad_words or [])
        for w in words:
            current.discard(w.lower().strip())
        automod.bad_words = list(current)
        await self.session.commit()
        await self.session.refresh(automod)
        return automod
