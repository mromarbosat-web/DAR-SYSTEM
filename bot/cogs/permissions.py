import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import Optional, List
from bot.database.connection import AsyncSessionLocal
from bot.services.permission_service import PermissionService
from bot.database.repositories.permission_repository import PermissionRepository
from bot.utils.embeds import EmbedBuilder

AVAILABLE_PERMISSIONS = [
    # Core Managers
    ("MODERATION_MANAGER", "Moderation Manager (إدارة الإشراف الشاملة)", "🔨"),
    ("VOICE_MANAGER", "Voice Manager (إدارة الصوت الشاملة)", "🎙️"),
    ("WARNING_MANAGER", "Warning Manager (إدارة التحذيرات الشاملة)", "⚠️"),
    
    # Detailed Warnings
    ("WARNING_ISSUE", "Warning: Issue (إصدار تحذير)", "📝"),
    ("WARNING_REMOVE", "Warning: Remove (حذف تحذير)", "🗑️"),
    ("WARNING_VIEW", "Warning: View (عرض التحذيرات)", "👁️"),
    
    # Detailed Moderation
    ("MOD_TIMEOUT", "Mod: Timeout (عزل مؤقت)", "⏱️"),
    ("MOD_KICK", "Mod: Kick (طرد)", "👢"),
    ("MOD_BAN", "Mod: Ban (حظر)", "🔨"),
    ("MOD_PURGE", "Mod: Purge (مسح رسائل)", "🧹"),
    ("MOD_SLOWMODE", "Mod: Slowmode (وضع بطيء)", "⏳"),
    ("MOD_LOCK_UNLOCK", "Mod: Lock/Unlock (قفل وفتح القنوات)", "🔒"),
    
    # Detailed Voice
    ("VOICE_LOCK_UNLOCK", "Voice: Lock/Unlock (قفل وفتح الرومات)", "🔐"),
    ("VOICE_MOVE", "Voice: Move (نقل)", "🔀"),
    ("VOICE_DISCONNECT", "Voice: Disconnect (فصل)", "🔌"),
    ("VOICE_MUTE_UNMUTE", "Voice: Mute/Unmute (كتم)", "🔇"),
    
    # Other Systems
    ("SECURITY_MANAGER", "Security Manager (إدارة الحماية)", "🛡️"),
    ("LOGS_MANAGER", "Logs Manager (إدارة السجلات)", "📋"),
    ("VERIFICATION_MANAGER", "Verification Manager (إدارة التحقق)", "✅"),
    ("AUTOMOD_MANAGER", "AutoMod Manager (إدارة الفلترة التلقائية)", "🤖"),
    ("ECONOMY_MANAGER", "Economy Manager (إدارة الاقتصاد)", "💰"),
]

class MultiPermissionRoleView(ui.View):
    """View that allows selecting multiple roles AND multiple permissions simultaneously."""
    def __init__(self, mode: str = "add"):
        super().__init__(timeout=300)
        self.mode = mode # 'add' or 'remove'
        self.selected_roles: List[discord.Role] = []
        self.selected_permissions: List[str] = []

        # Permission options (split into 25 max options)
        options = [
            discord.SelectOption(
                label=name[:100],
                value=val,
                emoji=emoji,
                description=f"صلاحية {val}"
            ) for val, name, emoji in AVAILABLE_PERMISSIONS[:25]
        ]

        self.perm_select = ui.Select(
            placeholder="اختر صلاحية واحدة أو أكثر (متعدد)...",
            min_values=1,
            max_values=len(options),
            options=options,
            row=1
        )
        self.perm_select.callback = self.perm_callback
        self.add_item(self.perm_select)

    @ui.select(cls=ui.RoleSelect, placeholder="اختر رتبة واحدة أو أكثر (حتى 10 رتب)...", min_values=1, max_values=10, row=0)
    async def role_select_callback(self, interaction: discord.Interaction, select: ui.RoleSelect):
        self.selected_roles = select.values
        await interaction.response.defer()

    async def perm_callback(self, interaction: discord.Interaction):
        self.selected_permissions = self.perm_select.values
        await interaction.response.defer()

    @ui.button(label="حفظ وتطبيق الصلاحيات المختارة", style=discord.ButtonStyle.success, emoji="💾", row=2)
    async def apply_btn(self, interaction: discord.Interaction, button: ui.Button):
        if not self.selected_roles:
            await interaction.response.send_message("❌ الرجاء اختيار رتبة واحدة على الأقل من القائمة الأولى!", ephemeral=True)
            return
        if not self.selected_permissions:
            await interaction.response.send_message("❌ الرجاء اختيار صلاحية واحدة على الأقل من القائمة الثانية!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            repo = PermissionRepository(session)
            success_count = 0
            already_count = 0

            for role in self.selected_roles:
                for perm in self.selected_permissions:
                    if self.mode == "add":
                        added = await repo.add_permission_role(interaction.guild.id, perm, role.id)
                        if added:
                            success_count += 1
                        else:
                            already_count += 1
                    else:
                        removed = await repo.remove_permission_role(interaction.guild.id, perm, role.id)
                        if removed:
                            success_count += 1

            roles_str = ", ".join([r.mention for r in self.selected_roles])
            perms_str = ", ".join([f"`{p}`" for p in self.selected_permissions])

            if self.mode == "add":
                msg = f"✅ تم بنجاح ربط **{len(self.selected_permissions)}** صلاحيات مع **{len(self.selected_roles)}** رتب:\n• **الرتب:** {roles_str}\n• **الصلاحيات:** {perms_str}"
                embed = EmbedBuilder.success("تم تخصيص الصلاحيات", msg)
            else:
                msg = f"🗑️ تم بنجاح إزالة الصلاحيات المختارة عن الرتب المحددة:\n• **الرتب:** {roles_str}\n• **الصلاحيات:** {perms_str}"
                embed = EmbedBuilder.success("تم إلغاء الصلاحيات", msg)

            await interaction.followup.send(embed=embed, ephemeral=True)

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

    @perm_group.command(name="set_manager", description="تخصيص وإعطاء أكثر من صلاحية لأكثر من رتبة دفعة واحدة عبر واجهة تفاعلية")
    @app_commands.describe(
        role="رتبة محددة (اختياري - يمكنك فتح القائمة لاختيار عدة رتب)",
        permission="صلاحية محددة (اختياري - يمكنك فتح القائمة لاختيار عدة صلاحيات)"
    )
    async def set_manager(
        self,
        interaction: discord.Interaction,
        role: Optional[discord.Role] = None,
        permission: Optional[str] = None
    ):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.is_server_admin(interaction.user):
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "هذا الأمر مخصص فقط لـ Server Admin ومالك السيرفر!"), ephemeral=True)
                return

            # If user directly passed both single role & permission, apply directly
            if role and permission:
                repo = PermissionRepository(session)
                added = await repo.add_permission_role(interaction.guild.id, permission, role.id)
                if added:
                    embed = EmbedBuilder.success("تم تخصيص الصلاحية", f"تم ربط صلاحية `{permission}` بالرتبة {role.mention} بنجاح.")
                else:
                    embed = EmbedBuilder.warning("تنبيه", f"الرتبة {role.mention} مسجلة بالفعل مع هذه الصلاحية!")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Open Multi-select interactive view
            view = MultiPermissionRoleView(mode="add")
            embed = discord.Embed(
                title="⚙️ تعيين وتخصيص صلاحيات متعددة لرتب متعددة",
                description=(
                    "يمكنك من خلال القوائم أدناه:\n"
                    "1️⃣ **اختيار رتب متعددة** من قائمة الرتب الأولى.\n"
                    "2️⃣ **اختيار صلاحيات متعددة** من قائمة الصلاحيات الثانية.\n"
                    "3️⃣ الضغط على زر **حفظ وتطبيق الصلاحيات** لربطها دفعة واحدة."
                ),
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @perm_group.command(name="remove_manager", description="إزالة صلاحيات متعددة عن رتب متعددة")
    @app_commands.describe(
        role="رتبة محددة (اختياري)",
        permission="صلاحية محددة (اختياري)"
    )
    async def remove_manager(
        self,
        interaction: discord.Interaction,
        role: Optional[discord.Role] = None,
        permission: Optional[str] = None
    ):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.is_server_admin(interaction.user):
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "هذا الأمر مخصص فقط لـ Server Admin ومالك السيرفر!"), ephemeral=True)
                return

            if role and permission:
                repo = PermissionRepository(session)
                removed = await repo.remove_permission_role(interaction.guild.id, permission, role.id)
                if removed:
                    embed = EmbedBuilder.success("تمت الإزالة", f"تم إلغاء صلاحية `{permission}` عن الرتبة {role.mention} بنجاح.")
                else:
                    embed = EmbedBuilder.error("خطأ", f"الرتبة {role.mention} لا تملك هذه الصلاحية بالأساس.")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            view = MultiPermissionRoleView(mode="remove")
            embed = discord.Embed(
                title="🗑️ إزالة وسحب صلاحيات من رتب متعددة",
                description="اختر الرتب والصلاحيات المراد سحبها ثم اضغط تطبيق:",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @perm_group.command(name="list_managers", description="عرض جدول كافة الرتب وتوزيع الصلاحيات المسندة إليها بالسيرفر")
    async def list_managers(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            repo = PermissionRepository(session)
            all_mappings = await repo.list_all_permissions(interaction.guild.id)

            if not all_mappings:
                embed = EmbedBuilder.info("جدول الصلاحيات", "لا توجد رتب إدارية مخصصة حتى الآن.")
            else:
                # Group by permission
                perm_dict = {}
                for perm, role_id in all_mappings:
                    perm_dict.setdefault(perm, []).append(f"<@&{role_id}>")

                lines = []
                for p, rlist in perm_dict.items():
                    lines.append(f"• **`{p}`**: {', '.join(rlist)}")

                embed = EmbedBuilder.info(
                    "جدول الصلاحيات المخصصة بالسيرفر",
                    "\n".join(lines)
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(PermissionAdminCog(bot))
