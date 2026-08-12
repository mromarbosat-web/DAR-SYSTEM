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

    @perm_group.command(name="set_manager", description="تخصيص رتبة لمدير نظام فرعي محدد (Manager Role)")
    @app_commands.describe(
        permission="نوع الصلاحية الفرعية",
        role="الرتبة الممنوحة"
    )
    @app_commands.choices(permission=[
        app_commands.Choice(name="Warning Manager (إدارة التحذيرات)", value="WARNING_MANAGER"),
        app_commands.Choice(name="Moderation Manager (إدارة الإشراف)", value="MODERATION_MANAGER"),
        app_commands.Choice(name="Security Manager (إدارة الحماية)", value="SECURITY_MANAGER"),
        app_commands.Choice(name="Voice Manager (إدارة الرومات الصوتية)", value="VOICE_MANAGER"),
        app_commands.Choice(name="Logs Manager (إدارة السجلات)", value="LOGS_MANAGER"),
        app_commands.Choice(name="Verification Manager (إدارة التحقق)", value="VERIFICATION_MANAGER"),
        app_commands.Choice(name="AutoMod Manager (إدارة الفلترة التلقائية)", value="AUTOMOD_MANAGER"),
        app_commands.Choice(name="Whitelist Manager (إدارة القائمة البيضاء)", value="WHITELIST_MANAGER"),
        app_commands.Choice(name="Settings Manager (إدارة الإعدادات)", value="SETTINGS_MANAGER"),
        app_commands.Choice(name="Role Manager (إدارة الرتب)", value="ROLE_MANAGER"),
        app_commands.Choice(name="Economy Manager (إدارة الاقتصاد)", value="ECONOMY_MANAGER"),
        app_commands.Choice(name="Shop Manager (إدارة المتجر)", value="SHOP_MANAGER"),
        app_commands.Choice(name="Transaction Viewer (عرض المعاملات المالية)", value="TRANSACTION_VIEWER"),
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

    @perm_group.command(name="remove_manager", description="إزالة رتبة من صلاحية مدير نظام فرعي")
    @app_commands.describe(
        permission="نوع الصلاحية الفرعية",
        role="الرتبة المراد سحب الصلاحية منها"
    )
    @app_commands.choices(permission=[
        app_commands.Choice(name="Warning Manager", value="WARNING_MANAGER"),
        app_commands.Choice(name="Moderation Manager", value="MODERATION_MANAGER"),
        app_commands.Choice(name="Security Manager", value="SECURITY_MANAGER"),
        app_commands.Choice(name="Voice Manager", value="VOICE_MANAGER"),
        app_commands.Choice(name="Logs Manager", value="LOGS_MANAGER"),
        app_commands.Choice(name="Verification Manager", value="VERIFICATION_MANAGER"),
        app_commands.Choice(name="AutoMod Manager", value="AUTOMOD_MANAGER"),
        app_commands.Choice(name="Whitelist Manager", value="WHITELIST_MANAGER"),
        app_commands.Choice(name="Settings Manager", value="SETTINGS_MANAGER"),
        app_commands.Choice(name="Role Manager", value="ROLE_MANAGER"),
        app_commands.Choice(name="Economy Manager", value="ECONOMY_MANAGER"),
        app_commands.Choice(name="Shop Manager", value="SHOP_MANAGER"),
        app_commands.Choice(name="Transaction Viewer", value="TRANSACTION_VIEWER"),
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
