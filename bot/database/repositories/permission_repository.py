import logging
from typing import List, Dict
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.permissions import GuildAdminRole, GuildPermissionRole

logger = logging.getLogger("discord_bot.permission_repository")

class PermissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_admin_role(self, guild_id: int, role_id: int) -> bool:
        stmt = select(GuildAdminRole).where(
            GuildAdminRole.guild_id == guild_id,
            GuildAdminRole.role_id == role_id
        )
        res = await self.session.execute(stmt)
        if res.scalar_one_or_none():
            return False

        admin_role = GuildAdminRole(guild_id=guild_id, role_id=role_id)
        self.session.add(admin_role)
        await self.session.commit()
        return True

    async def remove_admin_role(self, guild_id: int, role_id: int) -> bool:
        stmt = delete(GuildAdminRole).where(
            GuildAdminRole.guild_id == guild_id,
            GuildAdminRole.role_id == role_id
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount > 0

    async def get_admin_roles(self, guild_id: int) -> List[int]:
        stmt = select(GuildAdminRole.role_id).where(GuildAdminRole.guild_id == guild_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def add_permission_role(self, guild_id: int, permission_type: str, role_id: int) -> bool:
        perm_type = permission_type.upper().strip()
        stmt = select(GuildPermissionRole).where(
            GuildPermissionRole.guild_id == guild_id,
            GuildPermissionRole.permission_type == perm_type,
            GuildPermissionRole.role_id == role_id
        )
        res = await self.session.execute(stmt)
        if res.scalar_one_or_none():
            return False

        perm_role = GuildPermissionRole(
            guild_id=guild_id,
            permission_type=perm_type,
            role_id=role_id
        )
        self.session.add(perm_role)
        await self.session.commit()
        return True

    async def remove_permission_role(self, guild_id: int, permission_type: str, role_id: int) -> bool:
        perm_type = permission_type.upper().strip()
        stmt = delete(GuildPermissionRole).where(
            GuildPermissionRole.guild_id == guild_id,
            GuildPermissionRole.permission_type == perm_type,
            GuildPermissionRole.role_id == role_id
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount > 0

    async def get_permission_roles(self, guild_id: int, permission_type: str) -> List[int]:
        perm_type = permission_type.upper().strip()
        stmt = select(GuildPermissionRole.role_id).where(
            GuildPermissionRole.guild_id == guild_id,
            GuildPermissionRole.permission_type == perm_type
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_all_permission_roles(self, guild_id: int) -> Dict[str, List[int]]:
        stmt = select(GuildPermissionRole).where(GuildPermissionRole.guild_id == guild_id)
        res = await self.session.execute(stmt)
        roles = res.scalars().all()
        result: Dict[str, List[int]] = {}
        for r in roles:
            result.setdefault(r.permission_type, []).append(r.role_id)
        return result
