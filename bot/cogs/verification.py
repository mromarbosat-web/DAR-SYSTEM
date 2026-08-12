import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from bot.database.connection import AsyncSessionLocal
from bot.database.repositories.verification_repository import VerificationRepository
from bot.services.verification_service import VerificationService
from bot.utils.embeds import EmbedBuilder

class VerificationCog(commands.Cog):
    """Cog for Verification setup and panel management"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    verification_group = app_commands.Group(name="verification", description="أوامر وإعدادات نظام التحقق Verification")

    @verification_group.command(name="setup", description="إنشاء لوحة التحقق وتخصيص رتب الموثقين")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        channel="قناة إرسال لوحة التحقق",
        verified_role="الرتبة الممنوحة عند الضغط على زر التحقق",
        unverified_role="رتبة غير الموثقين المراد إزالتها (اختياري)",
        title="عنوان اللوحة (اختياري)",
        description="وصف اللوحة والتعليمات (اختياري)"
    )
    async def verification_setup(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        verified_role: discord.Role,
        unverified_role: Optional[discord.Role] = None,
        title: Optional[str] = None,
        description: Optional[str] = None
    ):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            service = VerificationService(session)
            msg = await service.setup_panel(
                guild=interaction.guild,
                channel=channel,
                verified_role=verified_role,
                unverified_role=unverified_role,
                title=title,
                description=description,
                session_factory=AsyncSessionLocal
            )

            embed = EmbedBuilder.success(
                title="تم إنشاء لوحة التحقق بنجاح",
                description=f"تم إرسال بنل التحقق بنجاح في القناة {channel.mention}.\n\n🔒 **Verified Role:** {verified_role.mention}"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @verification_group.command(name="status", description="عرض حالة إعدادات نظام التحقق")
    @app_commands.checks.has_permissions(administrator=True)
    async def verification_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            repo = VerificationRepository(session)
            verif = await repo.get_verification_settings(interaction.guild.id)

            status = "🟢 مفعّل (Enabled)" if verif and verif.enabled else "🔴 معطل (Disabled)"
            ch_mention = f"<#{verif.channel_id}>" if verif and verif.channel_id else "`غير محدد`"
            v_role = f"<@&{verif.verified_role_id}>" if verif and verif.verified_role_id else "`غير محدد`"
            uv_role = f"<@&{verif.unverified_role_id}>" if verif and verif.unverified_role_id else "`غير محدد`"

            fields = [
                ("الحالة", status, True),
                ("القناة", ch_mention, True),
                ("رتبة الموثق (Verified)", v_role, True),
                ("رتبة غير الموثق (Unverified)", uv_role, True)
            ]

            embed = EmbedBuilder.info(
                title=f"تقرير نظام التحقق لسيرفر {interaction.guild.name}",
                description="بيانات وإعدادات بنل التوثيق والتحقق بالأزرار",
                fields=fields
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(VerificationCog(bot))
