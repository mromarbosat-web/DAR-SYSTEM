import logging
from typing import Tuple, List, Optional
import discord
from sqlalchemy.ext.asyncio import AsyncSession
from bot.config.settings import settings
from bot.database.repositories.permission_repository import PermissionRepository

logger = logging.getLogger("discord_bot.permission_service")

class PermissionService:
    """
    Central permission authority for Security & Management Bot.
    Validates Bot Owners, Server Admins, Manager Roles, Discord Permissions, and Role Hierarchies.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.perm_repo = PermissionRepository(session)

    def is_bot_owner(self, user_id: int) -> bool:
        """Check if user is a registered Bot Owner"""
        return settings.is_bot_owner(user_id)

    async def is_server_admin(self, member: discord.Member) -> bool:
        """
        Check if member is a Server Admin.
        Returns True for:
        - Bot Owners
        - Guild Owner
        - Members with Administrator permission
        - Members holding any Server Admin role configured for the guild
        """
        if self.is_bot_owner(member.id):
            return True

        if not member.guild:
            return False

        if member.id == member.guild.owner_id:
            return True

        if member.guild_permissions.administrator:
            return True

        admin_role_ids = await self.perm_repo.get_admin_roles(member.guild.id)
        if admin_role_ids:
            member_role_ids = {r.id for r in member.roles}
            if any(rid in member_role_ids for rid in admin_role_ids):
                return True

        return False

    async def has_manager_permission(self, member: discord.Member, permission_type: str) -> bool:
        """
        Check if member has a specific manager permission (e.g., MODERATION_MANAGER, ECONOMY_MANAGER).
        Returns True for Bot Owners, Server Admins, or assigned role holders.
        """
        if self.is_bot_owner(member.id):
            return True

        if await self.is_server_admin(member):
            return True

        perm_roles = await self.perm_repo.get_permission_roles(member.guild.id, permission_type)
        if perm_roles:
            member_role_ids = {r.id for r in member.roles}
            if any(rid in member_role_ids for rid in perm_roles):
                return True

        return False

    def can_action_member(self, executor: discord.Member, target: discord.Member) -> Tuple[bool, str]:
        """
        Validates whether executor can perform moderation/administrative actions on target based on hierarchy.
        """
        if target.id == executor.guild.owner_id:
            return False, "لا يمكنك اتخاذ إجراء ضد مالك السيرفر!"

        if executor.id == target.id:
            return False, "لا يمكنك اتخاذ إجراء ضد نفسك!"

        if self.is_bot_owner(executor.id):
            return True, ""

        if executor.id == executor.guild.owner_id:
            return True, ""

        if executor.top_role.position <= target.top_role.position:
            return False, "لا يمكنك اتخاذ إجراء ضد عضو يمتلك رتبة مساوية أو أعلى من رتبتك!"

        return True, ""

    def bot_can_action_member(self, guild: discord.Guild, target: discord.Member) -> Tuple[bool, str]:
        """
        Validates if bot's top role position is higher than target member.
        """
        if target.id == guild.owner_id:
            return False, "لا يمكن للبوت اتخاذ إجراء ضد مالك السيرفر."

        bot_member = guild.me
        if not bot_member:
            return False, "عضوية البوت غير متاحة في السيرفر."

        if bot_member.top_role.position <= target.top_role.position:
            return False, "رتبة البوت أدنى من أو مساوية لرتبة العضو المستهدف!"

        return True, ""

    def can_manage_role(self, executor: discord.Member, role: discord.Role) -> Tuple[bool, str]:
        """
        Validates whether executor can assign/remove/modify/delete a role.
        """
        if role.is_default():
            return False, "لا يمكن تعديل رتبة الجميع (@everyone)!"

        if role.managed:
            return False, "لا يمكن تعديل رتبة مدمجة أو مدارة بواسطة بوتات/تطبيقات خارجية!"

        if self.is_bot_owner(executor.id):
            return True, ""

        if executor.id == executor.guild.owner_id:
            return True, ""

        if executor.top_role.position <= role.position:
            return False, "لا يمكنك إدارة رتبة مساوية أو أعلى من رتبتك الأكاديمية أعلى السيرفر!"

        return True, ""

    def bot_can_manage_role(self, guild: discord.Guild, role: discord.Role) -> Tuple[bool, str]:
        """
        Validates whether the bot has a higher top role position than the target role.
        """
        if role.is_default():
            return False, "البوت لا يمكنه التحكم في رتبة @everyone."

        if role.managed:
            return False, "البوت لا يمكنه التحكم في رتب البوتات التلقائية المدارة."

        bot_member = guild.me
        if not bot_member:
            return False, "البوت غير متاح في السيرفر."

        if not bot_member.guild_permissions.manage_roles:
            return False, "البوت لا يمتلك صلاحية إدارة الرتب (Manage Roles)!"

        if bot_member.top_role.position <= role.position:
            return False, "رتبة البوت الأفضلية أدنى من أو مساوية للرتبة المراد إدارتها!"

        return True, ""
