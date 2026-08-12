import discord
from discord import app_commands
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.database.repositories.automod_repository import AutoModRepository
from bot.services.setup_service import SetupService
from bot.utils.embeds import EmbedBuilder

class AutoModCog(commands.Cog):
    """Cog for AutoMod setup, status, and blacklist management"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    automod_group = app_commands.Group(name="automod", description="أوامر إدارة الإشراف التلقائي AutoMod")

    @automod_group.command(name="setup", description="ضبط إعدادات AutoMod والفلاتر التلقائية")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        enabled="تفعيل أو تعطيل نظام AutoMod",
        anti_spam="تفعيل حماية رسائل السبام السريعة",
        block_invites="منع روابط دعوات الديسكورد",
        block_links="منع الروابط الخارجية العامة",
        max_mentions="الحد الأقصى للمنشن المسموح به بالرسالة",
        max_messages_5s="أقصى عدد رسائل خلال 5 ثوانٍ",
        action="الإجراء المتخذ عند المخالفة"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Delete & Warn", value="delete_and_warn"),
            app_commands.Choice(name="Timeout User", value="timeout")
        ]
    )
    async def automod_setup(
        self,
        interaction: discord.Interaction,
        enabled: bool = None,
        anti_spam: bool = None,
        block_invites: bool = None,
        block_links: bool = None,
        max_mentions: int = None,
        max_messages_5s: int = None,
        action: app_commands.Choice[str] = None
    ):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        async with AsyncSessionLocal() as session:
            repo = AutoModRepository(session)
            
            kwargs = {}
            if enabled is not None: kwargs["enabled"] = enabled
            if anti_spam is not None: kwargs["anti_spam_enabled"] = anti_spam
            if block_invites is not None: kwargs["block_invites"] = block_invites
            if block_links is not None: kwargs["block_links"] = block_links
            if max_mentions is not None: kwargs["max_mentions"] = max_mentions
            if max_messages_5s is not None: kwargs["max_messages_per_5s"] = max_messages_5s
            if action is not None: kwargs["action"] = action.value

            await repo.update_automod_settings(guild.id, **kwargs)

            embed = EmbedBuilder.success(
                title="تم تحديث إعدادات AutoMod بنجاح",
                description="تم تطبيق وتحديث خيارات الإشراف التلقائي وفلترة المحتوى."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @automod_group.command(name="status", description="عرض تقرير حالة نظام AutoMod")
    @app_commands.checks.has_permissions(administrator=True)
    async def automod_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            setup_service = SetupService(session)
            embed = await setup_service.get_automod_status(interaction.guild)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @automod_group.command(name="badwords", description="إضافة أو إزالة كلمات محظورة من قائمة الفلترة")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(mode="نوع الإجراء (إضافة أو حذف)", words="الكلمات المفصولة بفواصل (مثال: كلمة1, كلمة2)")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="Add Words", value="add"),
            app_commands.Choice(name="Remove Words", value="remove")
        ]
    )
    async def automod_badwords(self, interaction: discord.Interaction, mode: app_commands.Choice[str], words: str):
        await interaction.response.defer(ephemeral=True)
        word_list = [w.strip() for w in words.split(",") if w.strip()]

        if not word_list:
            await interaction.followup.send("⚠️ يرجى إدخال كلمة واحدة على الأقل.", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            repo = AutoModRepository(session)
            if mode.value == "add":
                updated = await repo.add_bad_words(interaction.guild.id, word_list)
                msg = f"تمت إضافة `{len(word_list)}` كلمة إلى قائمة المحظورات."
            else:
                updated = await repo.remove_bad_words(interaction.guild.id, word_list)
                msg = f"تمت إزالة الكلمات من قائمة المحظورات."

            embed = EmbedBuilder.success(
                title="تم تحديث قائمة الكلمات المحظورة",
                description=f"{msg}\n**إجمالي الكلمات المحظورة حاليًا:** `{len(updated.bad_words or [])}`"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoModCog(bot))
