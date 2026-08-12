from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import VerificationSettings
from bot.database.repositories.guild_repository import GuildRepository

class VerificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_verification_settings(self, guild_id: int) -> VerificationSettings:
        stmt = select(VerificationSettings).where(VerificationSettings.guild_id == guild_id)
        result = await self.session.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            guild_repo = GuildRepository(self.session)
            await guild_repo.get_or_create_guild(guild_id, f"Guild_{guild_id}")
            result = await self.session.execute(stmt)
            settings = result.scalar_one_or_none()
        return settings

    async def update_verification_settings(self, guild_id: int, **kwargs) -> VerificationSettings:
        verif = await self.get_verification_settings(guild_id)
        for key, value in kwargs.items():
            if hasattr(verif, key) and value is not None:
                setattr(verif, key, value)
        await self.session.commit()
        await self.session.refresh(verif)
        return verif
