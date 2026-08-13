import discord
from discord import app_commands
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.permission_service import PermissionService
from bot.database.repositories.permission_repository import PermissionRepository
from bot.utils.embeds import EmbedBuilder

class PermissionAdminCog(commands.Cog):
    """Cog for Central Permission & Role Management Admin Commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    perm_group = app_commands.Group(name="permissions", description="إدارة صلاحيات الإدارة والرتب الإدارية العليا للبوت")

    @perm_group.command(name="set_admin_role", description="عيّن رتبة كـ Server Admin Role لتتيح لحامليها صلاحيات الإدارة الشاملة للبوت")
    @app_commands.describe(role="الرتبة المراد منحها صلاحية Server Admin")
    async def set_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.is_server_admin(interaction.user):
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "هذا الأمر مخصص فقط لـ Server Admin ومالك السيرفر!"), ephemeral=True)
                return

            repo = PermissionRepository(session)
            added = await repo.add_admin_role(interaction.guild.id, role.id)
            if added:
                embed = EmbedBuilder.success("تمت الإضافة", f"تم تعيين الرتبة {role.mention} كـ **Server Admin Role** بنجاح.")
            else:
                embed = EmbedBuilder.warning("تنبيه", f"الرتبة {role.mention} معينة بالفعل كـ Server Admin Role!")

            await interaction.followup.send(embed=embed, ephemeral=True)

    @perm_group.command(name="remove_admin_role", description="إلغاء رتبة Server Admin Role")
    @app_commands.describe(role="الرتبة المراد سحب صلاحية Server Admin منها")
    async def remove_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.is_server_admin(interaction.user):
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "هذا الأمر مخصص فقط لـ Server Admin ومالك السيرفر!"), ephemeral=True)
                return

            repo = PermissionRepository(session)
            removed = await repo.remove_admin_role(interaction.guild.id, role.id)
            if removed:
                embed = EmbedBuilder.success("تمت الإزالة", f"تم إلغاء صلاحية Server Admin عن الرتبة {role.mention} بنجاح.")
            else:
                embed = EmbedBuilder.error("خطأ", f"الرتبة {role.mention} ليست مسجلة كـ Server Admin Role بالأساس!")

            await interaction.followup.send(embed=embed, ephemeral=True)

    @perm_group.command(name="list_admin_roles", description="عرض جميع رتب Server Admin المسجلة بالسيرفر")
    async def list_admin_roles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            repo = PermissionRepository(session)
            role_ids = await repo.get_admin_roles(interaction.guild.id)

            if not role_ids:
                embed = EmbedBuilder.info("رتب Server Admin", "لا توجد رتب معينة كـ Server Admin حاليًا.")
            else:
                roles_mentions = [f"<@&{rid}> (`{rid}`)" for rid in role_ids]
                embed = EmbedBuilder.info(
                    "قائمة رتب Server Admin",
                    "الرتب التالية تمتلك صلاحيات الإدارة الشاملة للبوت داخل هذا السيرفر:\n" + "\n".join(roles_mentions)
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

    @perm_group.command(name="set_manager", description="تخصيص رتبة لمدير نظام فرعي أو صلاحية محددة (Permission Role)")
    @app_commands.describe(
        permission="نوع الصلاحية الممنوحة",
        role="الرتبة الممنوحة"
    )
    @app_commands.choices(permission=[
        # Core Managers
        app_commands.Choice(name="Moderation Manager (إدارة الإشراف الشاملة)", value="MODERATION_MANAGER"),
        app_commands.Choice(name="Voice Manager (إدارة الصوت الشاملة)", value="VOICE_MANAGER"),
        app_commands.Choice(name="Warning Manager (إدارة التحذيرات الشاملة)", value="WARNING_MANAGER"),
        
        # Detailed Warnings
        app_commands.Choice(name="Warning: Issue (إصدار تحذير)", value="WARNING_ISSUE"),
        app_commands.Choice(name="Warning: Remove (حذف تحذير)", value="WARNING_REMOVE"),
        app_commands.Choice(name="Warning: View (عرض التحذيرات)", value="WARNING_VIEW"),
        
        # Detailed Moderation
        app_commands.Choice(name="Mod: Timeout (عزل مؤقت)", value="MOD_TIMEOUT"),
        app_commands.Choice(name="Mod: Kick (طرد)", value="MOD_KICK"),
        app_commands.Choice(name="Mod: Ban (حظر)", value="MOD_BAN"),
        app_commands.Choice(name="Mod: Purge (مسح رسائل)", value="MOD_PURGE"),
        app_commands.Choice(name="Mod: Slowmode (وضع بطيء)", value="MOD_SLOWMODE"),
        app_commands.Choice(name="Mod: Lock/Unlock (قفل وفتح القنوات النصية)", value="MOD_LOCK_UNLOCK"),
        
        # Detailed Voice
        app_commands.Choice(name="Voice: Lock/Unlock (قفل وفتح الرومات الصوتية)", value="VOICE_LOCK_UNLOCK"),
        app_commands.Choice(name="Voice: Move (نقل)", value="VOICE_MOVE"),
        app_commands.Choice(name="Voice: Disconnect (فصل)", value="VOICE_DISCONNECT"),
        app_commands.Choice(name="Voice: Mute/Unmute (كتم)", value="VOICE_MUTE_UNMUTE"),
        
        # Other Systems
        app_commands.Choice(name="Security Manager (إدارة الحماية)", value="SECURITY_MANAGER"),
        app_commands.Choice(name="Logs Manager (إدارة السجلات)", value="LOGS_MANAGER"),
        app_commands.Choice(name="Verification Manager (إدارة التحقق)", value="VERIFICATION_MANAGER"),
        app_commands.Choice(name="AutoMod Manager (إدارة الفلترة التلقائية)", value="AUTOMOD_MANAGER"),
        app_commands.Choice(name="Economy Manager (إدارة الاقتصاد)", value="ECONOMY_MANAGER"),
    ])
    async def set_manager(self, interaction: discord.Interaction, permission: app_commands.Choice[str], role: discord.Role):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.is_server_admin(interaction.user):
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "هذا الأمر مخصص فقط لـ Server Admin ومالك السيرفر!"), ephemeral=True)
                return

            repo = PermissionRepository(session)
            added = await repo.add_permission_role(interaction.guild.id, permission.value, role.id)

            if added:
                embed = EmbedBuilder.success("تم تخصيص الصلاحية", f"تم ربط صلاحية `{permission.name}` بالرتبة {role.mention} بنجاح.")
            else:
                embed = EmbedBuilder.warning("تنبيه", f"الرتبة {role.mention} مسجلة بالفعل مع هذه الصلاحية!")

            await interaction.followup.send(embed=embed, ephemeral=True)

    @perm_group.command(name="remove_manager", description="إزالة رتبة من صلاحية محددة")
    @app_commands.describe(
        permission="نوع الصلاحية",
        role="الرتبة المراد سحب الصلاحية منها"
    )
    @app_commands.choices(permission=[
        app_commands.Choice(name="Moderation Manager", value="MODERATION_MANAGER"),
        app_commands.Choice(name="Voice Manager", value="VOICE_MANAGER"),
        app_commands.Choice(name="Warning Manager", value="WARNING_MANAGER"),
        app_commands.Choice(name="Warning: Issue", value="WARNING_ISSUE"),
        app_commands.Choice(name="Warning: Remove", value="WARNING_REMOVE"),
        app_commands.Choice(name="Warning: View", value="WARNING_VIEW"),
        app_commands.Choice(name="Mod: Timeout", value="MOD_TIMEOUT"),
        app_commands.Choice(name="Mod: Kick", value="MOD_KICK"),
        app_commands.Choice(name="Mod: Ban", value="MOD_BAN"),
        app_commands.Choice(name="Mod: Purge", value="MOD_PURGE"),
        app_commands.Choice(name="Mod: Slowmode", value="MOD_SLOWMODE"),
        app_commands.Choice(name="Mod: Lock/Unlock", value="MOD_LOCK_UNLOCK"),
        app_commands.Choice(name="Voice: Lock/Unlock", value="VOICE_LOCK_UNLOCK"),
        app_commands.Choice(name="Voice: Move", value="VOICE_MOVE"),
        app_commands.Choice(name="Voice: Disconnect", value="VOICE_DISCONNECT"),
        app_commands.Choice(name="Voice: Mute/Unmute", value="VOICE_MUTE_UNMUTE"),
        app_commands.Choice(name="Security Manager", value="SECURITY_MANAGER"),
        app_commands.Choice(name="Economy Manager", value="ECONOMY_MANAGER"),
    ])
    async def remove_manager(self, interaction: discord.Interaction, permission: app_commands.Choice[str], role: discord.Role):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.is_server_admin(interaction.user):
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "هذا الأمر مخصص فقط لـ Server Admin ومالك السيرفر!"), ephemeral=True)
                return

            repo = PermissionRepository(session)
            removed = await repo.remove_permission_role(interaction.guild.id, permission.value, role.id)

            if removed:
                embed = EmbedBuilder.success("تمت إزالة الصلاحية", f"تم فصل صلاحية `{permission.name}` عن الرتبة {role.mention} بنجاح.")
            else:
                embed = EmbedBuilder.error("خطأ", f"الرتبة {role.mention} ليست معينة مع صلاحية `{permission.name}` بالأساس!")

            await interaction.followup.send(embed=embed, ephemeral=True)

    @perm_group.command(name="list_managers", description="عرض جدول توزيع الصلاحيات ورتب المدراء في السيرفر")
    async def list_managers(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            repo = PermissionRepository(session)
            all_perms = await repo.get_all_permission_roles(interaction.guild.id)

            if not all_perms:
                embed = EmbedBuilder.info("جدول الصلاحيات الفرعية", "لم يتم تخصيص أي رتب لمدراء الأنظمة الفرعية بعد.")
            else:
                fields = []
                for ptype, rids in all_perms.items():
                    mentions = " ".join(f"<@&{rid}>" for rid in rids)
                    fields.append((f"⚙️ {ptype}", mentions, False))

                embed = EmbedBuilder.info(
                    "جدول رتب مدراء الأنظمة (Manager Roles)",
                    "توزيع الصلاحيات الإدارية الفرعية حسب الرتب في السيرفر:",
                    fields=fields
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(PermissionAdminCog(bot))
