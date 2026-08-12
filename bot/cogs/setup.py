import discord
from discord import app_commands
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.database.repositories.moderation_repository import ModerationRepository
from bot.utils.embeds import EmbedBuilder

class SetupCog(commands.Cog):
    """Cog for automatic punishment ladder setup"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    punishments_group = app_commands.Group(name="punishments", description="إعدادات سلم العقوبات التلقائية للتحذيرات")

    @punishments_group.command(name="setup", description="تخصيص العقوبات التلقائية عند وصول عدد التحذيرات لـ 3 أو 5 أو 7")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        warn_3="العقوبة عند الوصول لـ 3 تحذيرات",
        warn_5="العقوبة عند الوصول لـ 5 تحذيرات",
        warn_7="العقوبة عند الوصول لـ 7 تحذيرات"
    )
    @app_commands.choices(
        warn_3=[
            app_commands.Choice(name="Timeout 1 Hour", value="timeout_1h"),
            app_commands.Choice(name="Kick User", value="kick"),
            app_commands.Choice(name="Ban User", value="ban"),
            app_commands.Choice(name="None / No Action", value="none")
        ],
        warn_5=[
            app_commands.Choice(name="Timeout 1 Day", value="timeout_1d"),
            app_commands.Choice(name="Kick User", value="kick"),
            app_commands.Choice(name="Ban User", value="ban"),
            app_commands.Choice(name="None / No Action", value="none")
        ],
        warn_7=[
            app_commands.Choice(name="Ban User", value="ban"),
            app_commands.Choice(name="Kick User", value="kick"),
            app_commands.Choice(name="None / No Action", value="none")
        ]
    )
    async def punishments_setup(
        self,
        interaction: discord.Interaction,
        warn_3: app_commands.Choice[str] = None,
        warn_5: app_commands.Choice[str] = None,
        warn_7: app_commands.Choice[str] = None
    ):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            repo = ModerationRepository(session)
            kwargs = {}
            if warn_3: kwargs["warn_3_action"] = warn_3.value
            if warn_5: kwargs["warn_5_action"] = warn_5.value
            if warn_7: kwargs["warn_7_action"] = warn_7.value

            await repo.update_punishment_settings(interaction.guild.id, **kwargs)

            embed = EmbedBuilder.success(
                title="تم تحديث سلم العقوبات التلقائية",
                description="تم حفظ التغييرات الخاصة بالعقوبات المترتبة على تكرار التحذيرات."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @punishments_group.command(name="status", description="عرض جدول العقوبات التلقائية المعتمد حاليًا")
    @app_commands.checks.has_permissions(administrator=True)
    async def punishments_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            repo = ModerationRepository(session)
            p = await repo.get_punishment_settings(interaction.guild.id)

            fields = [
                ("⚠️ 3 التحذيرات الأولى", f"`{p.warn_3_action}`", True),
                ("⚠️ 5 تحذيرات", f"`{p.warn_5_action}`", True),
                ("🚨 7 تحذيرات", f"`{p.warn_7_action}`", True)
            ]

            embed = EmbedBuilder.info(
                title=f"سلم العقوبات لسيرفر {interaction.guild.name}",
                description="العقوبات التلقائية التي تُطبق فور تجاوز العضو لعدد محدد من التحذيرات.",
                fields=fields
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCog(bot))
