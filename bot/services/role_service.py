import logging
from typing import Tuple, Optional
import discord
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.permission_service import PermissionService
from bot.services.log_service import LogService
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.role_service")

class RoleService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.perm_service = PermissionService(session)
        self.log_service = LogService(session)

    async def add_role_to_member(
        self,
        guild: discord.Guild,
        executor: discord.Member,
        target: discord.Member,
        role: discord.Role
    ) -> Tuple[bool, str]:
        # 1. Check Manager Permission
        if not await self.perm_service.has_manager_permission(executor, "ROLE_MANAGER"):
            return False, "ليس لديك صلاحية إدارة الرتب (`ROLE_MANAGER`)!"

        # 2. Check User Hierarchy vs Target
        can_act, h_msg = self.perm_service.can_action_member(executor, target)
        if not can_act:
            return False, h_msg

        # 3. Check User Hierarchy vs Role
        can_role, r_msg = self.perm_service.can_manage_role(executor, role)
        if not can_role:
            return False, r_msg

        # 4. Check Bot Hierarchy vs Role
        bot_role, b_msg = self.perm_service.bot_can_manage_role(guild, role)
        if not bot_role:
            return False, b_msg

        if role in target.roles:
            return False, f"العضو {target.mention} يمتلك بالفعل رتبة {role.mention}!"

        try:
            await target.add_roles(role, reason=f"Role added by {executor} ({executor.id})")

            log_embed = EmbedBuilder.info(
                title="إضافة رتبة لعضو (Role Assigned)",
                description=f"تم إعطاء رتبة {role.mention} للعضو {target.mention}.",
                fields=[
                    ("العضو", f"{target} (`{target.id}`)", True),
                    ("المستجيب/المنفذ", f"{executor} (`{executor.id}`)", True),
                    ("الرتبة", f"{role.name} (`{role.id}`)", True)
                ]
            )
            await self.log_service.log_event(guild, "moderation", log_embed)
            return True, f"تم إعطاء رتبة {role.mention} للعضو {target.mention} بنجاح."
        except discord.Forbidden:
            return False, "فشلت العملية: البوت لا يمتلك الصلاحيات الكافية لتعديل رتبة هذا العضو!"
        except Exception as e:
            logger.error(f"Error adding role: {e}", exc_info=True)
            return False, f"حدث خطأ أثناء إضافة الرتبة: {e}"

    async def remove_role_from_member(
        self,
        guild: discord.Guild,
        executor: discord.Member,
        target: discord.Member,
        role: discord.Role
    ) -> Tuple[bool, str]:
        if not await self.perm_service.has_manager_permission(executor, "ROLE_MANAGER"):
            return False, "ليس لديك صلاحية إدارة الرتب (`ROLE_MANAGER`)!"

        can_act, h_msg = self.perm_service.can_action_member(executor, target)
        if not can_act:
            return False, h_msg

        can_role, r_msg = self.perm_service.can_manage_role(executor, role)
        if not can_role:
            return False, r_msg

        bot_role, b_msg = self.perm_service.bot_can_manage_role(guild, role)
        if not bot_role:
            return False, b_msg

        if role not in target.roles:
            return False, f"العضو {target.mention} لا يمتلك رتبة {role.mention} بالأساس!"

        try:
            await target.remove_roles(role, reason=f"Role removed by {executor} ({executor.id})")

            log_embed = EmbedBuilder.warning(
                title="إزالة رتبة من عضو (Role Removed)",
                description=f"تم سحب رتبة {role.mention} من العضو {target.mention}.",
                fields=[
                    ("العضو", f"{target} (`{target.id}`)", True),
                    ("المنفذ", f"{executor} (`{executor.id}`)", True),
                    ("الرتبة", f"{role.name} (`{role.id}`)", True)
                ]
            )
            await self.log_service.log_event(guild, "moderation", log_embed)
            return True, f"تم إزالة رتبة {role.mention} من العضو {target.mention} بنجاح."
        except discord.Forbidden:
            return False, "فشلت العملية: البوت لا يمتلك صلاحية سحب هذه الرتبة!"
        except Exception as e:
            logger.error(f"Error removing role: {e}", exc_info=True)
            return False, f"حدث خطأ أثناء إزالة الرتبة: {e}"

    async def rename_role(
        self,
        guild: discord.Guild,
        executor: discord.Member,
        role: discord.Role,
        new_name: str
    ) -> Tuple[bool, str]:
        if not await self.perm_service.has_manager_permission(executor, "ROLE_MANAGER"):
            return False, "ليس لديك صلاحية إدارة الرتب (`ROLE_MANAGER`)!"

        can_role, r_msg = self.perm_service.can_manage_role(executor, role)
        if not can_role:
            return False, r_msg

        bot_role, b_msg = self.perm_service.bot_can_manage_role(guild, role)
        if not bot_role:
            return False, b_msg

        old_name = role.name
        try:
            await role.edit(name=new_name.strip(), reason=f"Role renamed by {executor} ({executor.id})")

            log_embed = EmbedBuilder.info(
                title="تغيير اسم رتبة (Role Renamed)",
                description=f"تم تغيير اسم الرتبة من `{old_name}` إلى `{new_name}`.",
                fields=[
                    ("الرتبة", f"{role.mention} (`{role.id}`)", True),
                    ("المنفذ", f"{executor} (`{executor.id}`)", True)
                ]
            )
            await self.log_service.log_event(guild, "moderation", log_embed)
            return True, f"تم تغيير اسم الرتبة إلى `{new_name}` بنجاح."
        except Exception as e:
            logger.error(f"Error renaming role: {e}", exc_info=True)
            return False, f"حدث خطأ أثناء تغيير اسم الرتبة: {e}"

    async def change_role_color(
        self,
        guild: discord.Guild,
        executor: discord.Member,
        role: discord.Role,
        color_hex: str
    ) -> Tuple[bool, str]:
        if not await self.perm_service.has_manager_permission(executor, "ROLE_MANAGER"):
            return False, "ليس لديك صلاحية إدارة الرتب (`ROLE_MANAGER`)!"

        can_role, r_msg = self.perm_service.can_manage_role(executor, role)
        if not can_role:
            return False, r_msg

        bot_role, b_msg = self.perm_service.bot_can_manage_role(guild, role)
        if not bot_role:
            return False, b_msg

        clean_hex = color_hex.lstrip("#").strip()
        try:
            color_int = int(clean_hex, 16)
            discord_color = discord.Color(color_int)
        except ValueError:
            return False, "كود اللون غير صحيح! يرجى كتابة كود هكس مثل `#5865F2` أو `5865F2`."

        try:
            await role.edit(color=discord_color, reason=f"Role color changed by {executor} ({executor.id})")

            log_embed = EmbedBuilder.info(
                title="تغيير لون رتبة (Role Color Changed)",
                description=f"تم تغيير لون الرتبة {role.mention} إلى `#{clean_hex.upper()}`.",
                fields=[
                    ("الرتبة", f"{role.name} (`{role.id}`)", True),
                    ("المنفذ", f"{executor} (`{executor.id}`)", True)
                ]
            )
            await self.log_service.log_event(guild, "moderation", log_embed)
            return True, f"تم تغيير لون الرتبة {role.mention} إلى `#{clean_hex.upper()}` بنجاح."
        except Exception as e:
            logger.error(f"Error changing role color: {e}", exc_info=True)
            return False, f"حدث خطأ أثناء تغيير لون الرتبة: {e}"

    async def create_role(
        self,
        guild: discord.Guild,
        executor: discord.Member,
        name: str,
        color_hex: Optional[str] = None
    ) -> Tuple[bool, str, Optional[discord.Role]]:
        if not await self.perm_service.has_manager_permission(executor, "ROLE_MANAGER"):
            return False, "ليس لديك صلاحية إدارة الرتب (`ROLE_MANAGER`)!", None

        bot_member = guild.me
        if not bot_member or not bot_member.guild_permissions.manage_roles:
            return False, "البوت لا يمتلك صلاحية إدارة الرتب (Manage Roles) لإنشاء رتبة جديدة!", None

        discord_color = discord.Color.default()
        if color_hex:
            clean_hex = color_hex.lstrip("#").strip()
            try:
                discord_color = discord.Color(int(clean_hex, 16))
            except ValueError:
                return False, "كود اللون الهكس المرفق غير صحيح!", None

        try:
            new_role = await guild.create_role(
                name=name.strip(),
                color=discord_color,
                reason=f"Role created by {executor} ({executor.id})"
            )

            log_embed = EmbedBuilder.success(
                title="إنشاء رتبة جديدة (Role Created)",
                description=f"تم إنشاء رتبة جديدة باسم `{new_role.name}`.",
                fields=[
                    ("الرتبة", f"{new_role.mention} (`{new_role.id}`)", True),
                    ("المنفذ", f"{executor} (`{executor.id}`)", True)
                ]
            )
            await self.log_service.log_event(guild, "moderation", log_embed)
            return True, f"تم إنشاء الرتبة الجديدة {new_role.mention} بنجاح.", new_role
        except Exception as e:
            logger.error(f"Error creating role: {e}", exc_info=True)
            return False, f"حدث خطأ أثناء إنشاء الرتبة: {e}", None

    async def delete_role(
        self,
        guild: discord.Guild,
        executor: discord.Member,
        role: discord.Role
    ) -> Tuple[bool, str]:
        if not await self.perm_service.has_manager_permission(executor, "ROLE_MANAGER"):
            return False, "ليس لديك صلاحية إدارة الرتب (`ROLE_MANAGER`)!"

        can_role, r_msg = self.perm_service.can_manage_role(executor, role)
        if not can_role:
            return False, r_msg

        bot_role, b_msg = self.perm_service.bot_can_manage_role(guild, role)
        if not bot_role:
            return False, b_msg

        role_name = role.name
        role_id = role.id

        try:
            await role.delete(reason=f"Role deleted by {executor} ({executor.id})")

            log_embed = EmbedBuilder.error(
                title="حذف رتبة (Role Deleted)",
                description=f"تم حذف الرتبة `{role_name}` (`{role_id}`) من السيرفر.",
                fields=[
                    ("اسم الرتبة المحذوفة", f"`{role_name}`", True),
                    ("معرف الرتبة", f"`{role_id}`", True),
                    ("المنفذ", f"{executor} (`{executor.id}`)", True)
                ]
            )
            await self.log_service.log_event(guild, "moderation", log_embed)
            return True, f"تم حذف الرتبة `{role_name}` بنجاح."
        except Exception as e:
            logger.error(f"Error deleting role: {e}", exc_info=True)
            return False, f"حدث خطأ أثناء حذف الرتبة: {e}"
