import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from bot.database.connection import AsyncSessionLocal
from bot.database.repositories.log_repository import LogRepository
from bot.services.setup_service import SetupService
from bot.utils.embeds import EmbedBuilder

class LogsCog(commands.Cog):
    """Cog for Logs channel setup and status"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    logs_group = app_commands.Group(name="logs", description="أوامر وقنوات السجلات واللوجز")

    @logs_group.command(name="setup", description="تعيين القناة المخصصة لنوع معين من السجلات")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        log_type="نوع السجل المراد تخصيص القناة له",
        channel="القناة المراد إرسال اللوجز إليها (أو اتركها فارغة لإلغاء القناة)"
    )
    @app_commands.choices(
        log_type=[
            app_commands.Choice(name="Member Logs (دخول/خروج/رتب الأعضاء)", value="member"),
            app_commands.Choice(name="Message Logs (حذف وتعديل الرسائل)", value="message"),
            app_commands.Choice(name="Moderation Logs (أوامر العقوبات والتحذيرات)", value="moderation"),
            app_commands.Choice(name="Role Logs (إنشاء وتعديل وحذف الرتب)", value="role"),
            app_commands.Choice(name="Channel Logs (إنشاء وتعديل وحذف القنوات)", value="channel"),
            app_commands.Choice(name="Server Logs (إعدادات السيرفر والـ Webhooks)", value="server"),
            app_commands.Choice(name="Security Logs (Anti-Raid & Anti-Nuke & AutoMod)", value="security")
        ]
    )
    async def logs_setup(
        self,
        interaction: discord.Interaction,
        log_type: app_commands.Choice[str],
        channel: Optional[discord.TextChannel] = None
    ):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            repo = LogRepository(session)
            ch_id = channel.id if channel else None
            await repo.update_log_channel(interaction.guild.id, log_type.value, ch_id)

            if channel:
                msg = f"تم تعيين القناة {channel.mention} لنوع السجل `{log_type.name}`."
            else:
                msg = f"تم تعطيل وإلغاء القناة المخصصة لـ `{log_type.name}`."

            embed = EmbedBuilder.success("تم تحديث إعدادات اللوجز", msg)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @logs_group.command(name="status", description="عرض القنوات المخصصة لكل أنواع اللوجز في السيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    async def logs_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            service = SetupService(session)
            embed = await service.get_logs_status(interaction.guild)
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(LogsCog(bot))
