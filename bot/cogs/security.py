import discord
from discord import app_commands
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.database.repositories.security_repository import SecurityRepository
from bot.services.security_service import SecurityService
from bot.services.setup_service import SetupService
from bot.utils.embeds import EmbedBuilder

class SecurityCog(commands.Cog):
    """Cogs handling Security, Anti-Raid, Anti-Nuke, Lockdown and Unlock"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    security_group = app_commands.Group(name="security", description="أوامر الحماية والأمان الإداري")

    @security_group.command(name="setup", description="ضبط إعدادات Anti-Raid و Anti-Nuke")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        anti_raid="تفعيل أو تعطيل حماية Anti-Raid",
        raid_threshold="عدد الأعضاء المطلوبة لتفعيل Anti-Raid",
        raid_window="النافذة الزمنية بالثواني لاكتشاف Anti-Raid",
        raid_action="الإجراء الوقائي عند اكتشاف Raid",
        anti_nuke="تفعيل أو تعطيل حماية Anti-Nuke",
        nuke_channel_threshold="عدد القنوات المسموح بحذفها خلال المدة",
        nuke_role_threshold="عدد الرتب المسموح بحذفها خلال المدة",
        nuke_action="الإجراء الوقائي ضد المنفذ"
    )
    @app_commands.choices(
        raid_action=[
            app_commands.Choice(name="Lockdown Channels", value="lockdown"),
            app_commands.Choice(name="Kick New Members", value="kick"),
            app_commands.Choice(name="Ban New Members", value="ban"),
            app_commands.Choice(name="Timeout New Members", value="timeout")
        ],
        nuke_action=[
            app_commands.Choice(name="Remove Dangerous Roles", value="remove_roles"),
            app_commands.Choice(name="Ban Offender", value="ban")
        ]
    )
    async def security_setup(
        self,
        interaction: discord.Interaction,
        anti_raid: bool = None,
        raid_threshold: int = None,
        raid_window: int = None,
        raid_action: app_commands.Choice[str] = None,
        anti_nuke: bool = None,
        nuke_channel_threshold: int = None,
        nuke_role_threshold: int = None,
        nuke_action: app_commands.Choice[str] = None
    ):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        async with AsyncSessionLocal() as session:
            repo = SecurityRepository(session)
            
            if anti_raid is not None or raid_threshold or raid_window or raid_action:
                await repo.update_anti_raid(
                    guild_id=guild.id,
                    enabled=anti_raid,
                    threshold=raid_threshold,
                    window=raid_window,
                    action=raid_action.value if raid_action else None
                )

            if anti_nuke is not None or nuke_channel_threshold or nuke_role_threshold or nuke_action:
                await repo.update_anti_nuke(
                    guild_id=guild.id,
                    enabled=anti_nuke,
                    channel_threshold=nuke_channel_threshold,
                    role_threshold=nuke_role_threshold,
                    action=nuke_action.value if nuke_action else None
                )

            embed = EmbedBuilder.success(
                title="تم تحديث إعدادات الأمان بنجاح",
                description="تم حفظ التغييرات الخاصة بنظام الحماية Anti-Raid و Anti-Nuke في قاعدة البيانات."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @security_group.command(name="status", description="عرض حالة الإعدادات الأمنية للسيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    async def security_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            setup_service = SetupService(session)
            embed = await setup_service.get_security_status(interaction.guild)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="lock", description="إغلاق القناة الحالية أو كافة القنوات بمنع إرسال الرسائل")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(all_channels="هل تريد إغلاق كل القنوات النصية في السيرفر؟", reason="سبب الإغلاق")
    async def lock_command(self, interaction: discord.Interaction, all_channels: bool = False, reason: str = "Lockdown by Moderator"):
        await interaction.response.defer()
        guild = interaction.guild

        async with AsyncSessionLocal() as session:
            sec_service = SecurityService(session)
            if all_channels:
                await sec_service.lockdown_guild(guild, reason=reason)
                embed = EmbedBuilder.warning(
                    title="تم إغلاق كافة قنوات السيرفر (Server Lockdown Active)",
                    description=f"تم تطبيق الإغلاق الشامل على جميع القنوات النصية.\n**السبب:** {reason}"
                )
            else:
                channel = interaction.channel
                overwrites = channel.overwrites_for(guild.default_role)
                overwrites.send_messages = False
                await channel.set_permissions(guild.default_role, overwrite=overwrites, reason=reason)
                embed = EmbedBuilder.warning(
                    title="تم إغلاق القناة (Channel Locked)",
                    description=f"تم منع إرسال الرسائل في القناة {channel.mention}.\n**السبب:** {reason}"
                )

            await interaction.followup.send(embed=embed)

    @app_commands.command(name="unlock", description="فتح القناة الحالية أو كافة القنوات بالسماح بإرسال الرسائل")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(all_channels="هل تريد فتح كل القنوات النصية في السيرفر؟")
    async def unlock_command(self, interaction: discord.Interaction, all_channels: bool = False):
        await interaction.response.defer()
        guild = interaction.guild

        async with AsyncSessionLocal() as session:
            sec_service = SecurityService(session)
            if all_channels:
                await sec_service.unlock_guild(guild, reason="Unlock by Moderator")
                embed = EmbedBuilder.success(
                    title="تم إلغاء الإغلاق الشامل (Server Unlocked)",
                    description="تم فتح كافة القنوات النصية وإتاحة الكتابة مجددًا."
                )
            else:
                channel = interaction.channel
                overwrites = channel.overwrites_for(guild.default_role)
                overwrites.send_messages = None
                await channel.set_permissions(guild.default_role, overwrite=overwrites, reason="Unlock by Moderator")
                embed = EmbedBuilder.success(
                    title="تم فتح القناة (Channel Unlocked)",
                    description=f"تمت إعادة فتح القناة {channel.mention} للكتابة."
                )

            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(SecurityCog(bot))
