import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from bot.database.connection import AsyncSessionLocal
from bot.database.repositories.whitelist_repository import WhitelistRepository
from bot.utils.embeds import EmbedBuilder

class WhitelistCog(commands.Cog):
    """Cog for managing Whitelist for Users, Roles, and Bots"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    whitelist_group = app_commands.Group(name="whitelist", description="إدارة قائمة الاستثناءات الموثوقة (Whitelist)")

    @whitelist_group.command(name="user", description="إضافة أو إزالة عضو من القائمة البيضاء (تجاوز الحماية)")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        action="نوع الإجراء (إضافة أو حذف)",
        user="العضو المراد إضافته أو إزالته",
        reason="سبب الاستثناء"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Add User", value="add"),
            app_commands.Choice(name="Remove User", value="remove")
        ]
    )
    async def whitelist_user(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        user: discord.User,
        reason: Optional[str] = "Trusted User Whitelist"
    ):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            repo = WhitelistRepository(session)
            if action.value == "add":
                try:
                    await repo.add_user(interaction.guild.id, user.id, interaction.user.id, reason)
                    embed = EmbedBuilder.success("تمت الإضافة للقائمة البيضاء", f"تمت إضافة العضو {user.mention} إلى قائمة الاستثناء الموثوقة بنجاح.")
                except Exception:
                    embed = EmbedBuilder.warning("موجود بالفعل", f"العضو {user.mention} موجود بالفعل في القائمة البيضاء.")
            else:
                removed = await repo.remove_user(interaction.guild.id, user.id)
                if removed:
                    embed = EmbedBuilder.success("تمت الإزالة من القائمة البيضاء", f"تمت إزالة العضو {user.mention} من قائمة الاستثناء.")
                else:
                    embed = EmbedBuilder.error("غير موجود", f"العضو {user.mention} غير موجود بالقائمة البيضاء.")

            await interaction.followup.send(embed=embed, ephemeral=True)

    @whitelist_group.command(name="role", description="إضافة أو إزالة رتبة كاملة من القائمة البيضاء")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        action="نوع الإجراء (إضافة أو حذف)",
        role="الرتبة الاستثنائية",
        reason="السبب"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Add Role", value="add"),
            app_commands.Choice(name="Remove Role", value="remove")
        ]
    )
    async def whitelist_role(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        role: discord.Role,
        reason: Optional[str] = "Trusted Role Whitelist"
    ):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            repo = WhitelistRepository(session)
            if action.value == "add":
                try:
                    await repo.add_role(interaction.guild.id, role.id, interaction.user.id, reason)
                    embed = EmbedBuilder.success("تمت إضافتها للقائمة البيضاء", f"تمت إضافة الرتبة {role.mention} إلى قائمة الاستثناء بنجاح.")
                except Exception:
                    embed = EmbedBuilder.warning("موجودة بالفعل", f"الرتبة {role.mention} موجودة بالفعل بالقائمة البيضاء.")
            else:
                removed = await repo.remove_role(interaction.guild.id, role.id)
                if removed:
                    embed = EmbedBuilder.success("تمت الإزالة من القائمة البيضاء", f"تمت إزالة الرتبة {role.mention} من قائمة الاستثناء.")
                else:
                    embed = EmbedBuilder.error("غير موجودة", f"الرتبة {role.mention} غير موجودة بالقائمة البيضاء.")

            await interaction.followup.send(embed=embed, ephemeral=True)

    @whitelist_group.command(name="list", description="استعراض الأعضاء والرتب المضافة إلى القائمة البيضاء")
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            repo = WhitelistRepository(session)
            users = await repo.get_all_whitelisted_users(interaction.guild.id)
            roles = await repo.get_all_whitelisted_roles(interaction.guild.id)

            u_text = "\n".join([f"• <@{u.user_id}> (`{u.user_id}`)" for u in users]) if users else "*لا يوجد أعضاء مستثنون*"
            r_text = "\n".join([f"• <@&{r.role_id}> (`{r.role_id}`)" for r in roles]) if roles else "*لا توجد رتب مستثناة*"

            fields = [
                ("👤 الأعضاء الموثوقون (Users)", u_text, False),
                ("🎭 الرتب الموثوقة (Roles)", r_text, False)
            ]

            embed = EmbedBuilder.info(
                title=f"قائمة الاستثناءات والـ Whitelist لسيرفر {interaction.guild.name}",
                description="الأعضاء والرتب المعفاة من قيود Anti-Raid و Anti-Nuke و AutoMod.",
                fields=fields
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(WhitelistCog(bot))
