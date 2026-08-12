from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import WhitelistedUser, WhitelistedRole, WhitelistedBot, GuildRepository

class WhitelistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_whitelisted(self, guild_id: int, user_id: int, role_ids: List[int] = None) -> bool:
        role_ids = role_ids or []
        
        # Check User Whitelist
        user_stmt = select(WhitelistedUser).where(
            WhitelistedUser.guild_id == guild_id,
            WhitelistedUser.user_id == user_id
        )
        u_res = await self.session.execute(user_stmt)
        if u_res.scalar_one_or_none():
            return True

        # Check Bot Whitelist
        bot_stmt = select(WhitelistedBot).where(
            WhitelistedBot.guild_id == guild_id,
            WhitelistedBot.bot_id == user_id
        )
        b_res = await self.session.execute(bot_stmt)
        if b_res.scalar_one_or_none():
            return True

        # Check Role Whitelist
        if role_ids:
            role_stmt = select(WhitelistedRole).where(
                WhitelistedRole.guild_id == guild_id,
                WhitelistedRole.role_id.in_(role_ids)
            )
            r_res = await self.session.execute(role_stmt)
            if r_res.scalars().all():
                return True

        return False

    async def add_user(self, guild_id: int, user_id: int, added_by: int, reason: Optional[str] = None) -> WhitelistedUser:
        guild_repo = GuildRepository(self.session)
        await guild_repo.get_or_create_guild(guild_id, f"Guild_{guild_id}")
        
        entry = WhitelistedUser(guild_id=guild_id, user_id=user_id, added_by=added_by, reason=reason)
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def remove_user(self, guild_id: int, user_id: int) -> bool:
        stmt = delete(WhitelistedUser).where(
            WhitelistedUser.guild_id == guild_id,
            WhitelistedUser.user_id == user_id
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount > 0

    async def add_role(self, guild_id: int, role_id: int, added_by: int, reason: Optional[str] = None) -> WhitelistedRole:
        guild_repo = GuildRepository(self.session)
        await guild_repo.get_or_create_guild(guild_id, f"Guild_{guild_id}")

        entry = WhitelistedRole(guild_id=guild_id, role_id=role_id, added_by=added_by, reason=reason)
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def remove_role(self, guild_id: int, role_id: int) -> bool:
        stmt = delete(WhitelistedRole).where(
            WhitelistedRole.guild_id == guild_id,
            WhitelistedRole.role_id == role_id
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount > 0

    async def get_all_whitelisted_users(self, guild_id: int) -> List[WhitelistedUser]:
        stmt = select(WhitelistedUser).where(WhitelistedUser.guild_id == guild_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_all_whitelisted_roles(self, guild_id: int) -> List[WhitelistedRole]:
        stmt = select(WhitelistedRole).where(WhitelistedRole.guild_id == guild_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
