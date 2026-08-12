from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import Guild, GuildSettings, SecuritySettings, AutoModSettings, VerificationSettings, LogSettings, PunishmentSettings

class GuildRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_guild(self, guild_id: int, guild_name: str) -> Guild:
        stmt = select(Guild).where(Guild.guild_id == guild_id)
        result = await self.session.execute(stmt)
        guild = result.scalar_one_or_none()

        if not guild:
            guild = Guild(guild_id=guild_id, name=guild_name, is_active=True)
            self.session.add(guild)
            
            # Initialize default settings records for all modules
            settings = GuildSettings(guild_id=guild_id)
            sec_settings = SecuritySettings(guild_id=guild_id)
            automod_settings = AutoModSettings(guild_id=guild_id)
            verif_settings = VerificationSettings(guild_id=guild_id)
            log_settings = LogSettings(guild_id=guild_id)
            punish_settings = PunishmentSettings(guild_id=guild_id)

            self.session.add_all([
                settings, sec_settings, automod_settings,
                verif_settings, log_settings, punish_settings
            ])
            await self.session.commit()
            await self.session.refresh(guild)
        else:
            if guild.name != guild_name or not guild.is_active:
                guild.name = guild_name
                guild.is_active = True
                await self.session.commit()

        return guild

    async def get_guild_settings(self, guild_id: int) -> Optional[GuildSettings]:
        stmt = select(GuildSettings).where(GuildSettings.guild_id == guild_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
