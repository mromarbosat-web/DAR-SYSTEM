import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from bot.database.connection import AsyncSessionLocal
from bot.services.role_service import RoleService
from bot.utils.embeds import EmbedBuilder

class ConfirmRoleDeleteView(discord.ui.View):
    def __init__(self, inviter_id: int, role: discord.Role, role_service: RoleService):
        super().__init__(timeout=60)
        self.inviter_id = inviter_id
        self.role = role
        self.role_service = role_service
        self.confirmed: Optional[bool] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.inviter_id:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("عذراً", "لا يمكنك التفاعل مع هذا الزر لأنك لست صاحب الأمر!"),
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="تأكيد الحذف (Confirm Delete)", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.confirmed = True
        self.stop()

        success, msg = await self.role_service.delete_role(interaction.guild, interaction.user, self.role)
        if success:
            embed = EmbedBuilder.success("تم حذف الرتبة", msg)
        else:
            embed = EmbedBuilder.error("فشل حذف الرتبة", msg)

        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="إلغاء (Cancel)", style=discord.ButtonStyle.secondary, emoji="✖️")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.confirmed = False
        self.stop()

        embed = EmbedBuilder.info("تم إلغاء العملية", f"تم إلغاء عملية حذف الرتبة `{self.role.name}` بناءً على طلبك.")
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(embed=embed, view=self)

class RoleManagementCog(commands.Cog):
    """Cog for full Role Administration Commands (/role)"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    role_group = app_commands.Group(name="role", description="أوامر إدارة الرتب والأعضاء في السيرفر")

    @role_group.command(name="add", description="إضافة رتبة لعضو محدد في السيرفر")
    @app_commands.describe(user="العضو المستهدف", role="الرتبة المراد إعطاؤها")
    async def role_add(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            role_service = RoleService(session)
            success, msg = await role_service.add_role_to_member(interaction.guild, interaction.user, user, role)

            if success:
                embed = EmbedBuilder.success("تمت إضافة الرتبة", msg)
            else:
                embed = EmbedBuilder.error("تعذر إضافة الرتبة", msg)

            await interaction.followup.send(embed=embed)

    @role_group.command(name="remove", description="إزالة رتبة من عضو محدد في السيرفر")
    @app_commands.describe(user="العضو المستهدف", role="الرتبة المراد سحبها")
    async def role_remove(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            role_service = RoleService(session)
            success, msg = await role_service.remove_role_from_member(interaction.guild, interaction.user, user, role)

            if success:
                embed = EmbedBuilder.success("تمت إزالة الرتبة", msg)
            else:
                embed = EmbedBuilder.error("تعذر إزالة الرتبة", msg)

            await interaction.followup.send(embed=embed)

    @role_group.command(name="rename", description="تغيير اسم رتبة في السيرفر")
    @app_commands.describe(role="الرتبة المستهدفة", name="الاسم الجديد للرتبة")
    async def role_rename(self, interaction: discord.Interaction, role: discord.Role, name: str):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            role_service = RoleService(session)
            success, msg = await role_service.rename_role(interaction.guild, interaction.user, role, name)

            if success:
                embed = EmbedBuilder.success("تم تغيير اسم الرتبة", msg)
            else:
                embed = EmbedBuilder.error("تعذر تغيير الاسم", msg)

            await interaction.followup.send(embed=embed)

    @role_group.command(name="color", description="تغيير لون رتبة باستخدام كود اللون (Hex)")
    @app_commands.describe(role="الرتبة المستهدفة", color="كود اللون الهكس (مثال: #5865F2)")
    async def role_color(self, interaction: discord.Interaction, role: discord.Role, color: str):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            role_service = RoleService(session)
            success, msg = await role_service.change_role_color(interaction.guild, interaction.user, role, color)

            if success:
                embed = EmbedBuilder.success("تم تغيير لون الرتبة", msg)
            else:
                embed = EmbedBuilder.error("تعذر تغيير اللون", msg)

            await interaction.followup.send(embed=embed)

    @role_group.command(name="create", description="إنشاء رتبة جديدة في السيرفر")
    @app_commands.describe(name="اسم الرتبة الجديدة", color="لون الرتبة اختياريًا (مثال: #FF0000)")
    async def role_create(self, interaction: discord.Interaction, name: str, color: Optional[str] = None):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            role_service = RoleService(session)
            success, msg, _ = await role_service.create_role(interaction.guild, interaction.user, name, color)

            if success:
                embed = EmbedBuilder.success("تم إنشاء الرتبة", msg)
            else:
                embed = EmbedBuilder.error("تعذر إنشاء الرتبة", msg)

            await interaction.followup.send(embed=embed)

    @role_group.command(name="delete", description="حذف رتبة من السيرفر مع زر التأكيد")
    @app_commands.describe(role="الرتبة المراد حذفها")
    async def role_delete(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            role_service = RoleService(session)
            # Perform initial permission & hierarchy checks before displaying confirmation view
            can_manage, r_msg = role_service.perm_service.can_manage_role(interaction.user, role)
            if not can_manage:
                await interaction.followup.send(embed=EmbedBuilder.error("تعذر التنفيذ", r_msg))
                return

            bot_can, b_msg = role_service.perm_service.bot_can_manage_role(interaction.guild, role)
            if not bot_can:
                await interaction.followup.send(embed=EmbedBuilder.error("تعذر التنفيذ", b_msg))
                return

            embed = EmbedBuilder.warning(
                title="تأكيد حذف الرتبة",
                description=f"هل أنت متأكد تمامًا من رغبتك في حذف الرتبة {role.mention} (`{role.id}`)؟\n⚠️ **هذا الإجراء نهائي ولا يمكن التراجع عنه.**"
            )
            view = ConfirmRoleDeleteView(interaction.user.id, role, role_service)
            await interaction.followup.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(RoleManagementCog(bot))
