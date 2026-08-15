import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import Optional, List, Union
from datetime import timedelta

from bot.config.settings import settings
from bot.database.connection import AsyncSessionLocal
from bot.services.moderation_service import ModerationService
from bot.services.warning_service import WarningService
from bot.services.voice_service import VoiceService
from bot.services.permission_service import PermissionService
from bot.services.security_service import SecurityService
from bot.services.automod_service import AutoModService
from bot.services.log_service import LogService
from bot.services.economy_service import EconomyService
from bot.services.shop_service import ShopService
from bot.database.repositories.shortcut_repository import ShortcutRepository
from bot.utils.embeds import EmbedBuilder
from bot.cogs.profile import BannerCarouselView

def build_main_control_embed(guild: discord.Guild, user: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="🛡️ لوحة التحكم الشاملة | Discord Control Center",
        description=(
            "مرحباً بك في لوحة التحكم الإدارية الشاملة والمباشرة.\n"
            "كافة الأزرار والأقسام أدناه تفاعلية بالكامل للتحكم الفوري في الحماية، الأوتومود، اللوجات، الاقتصاد، واختصارات الأوامر."
        ),
        color=discord.Color.from_rgb(88, 101, 242)
    )
    embed.add_field(name="🌐 السيرفر", value=f"**{guild.name}**", inline=True)
    embed.add_field(name="👮 المسؤول", value=user.mention, inline=True)
    embed.add_field(name="✨ العملة الرسمية", value=f"**{settings.CURRENCY_NAME}** {settings.CURRENCY_EMOJI}", inline=True)
    embed.set_footer(text="استخدم الأزرار للتنقل والتحكم المباشر")
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    return embed

class ControlCog(commands.Cog):
    """Cog providing an Interactive Discord-based Control Panel for server management."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="control", description="فتح لوحة التحكم الإدارية الشاملة والتفاعلية للسيرفر")
    async def control_panel(self, interaction: discord.Interaction):
        """Main entry point for the Discord Control Panel."""
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            is_admin = interaction.user.guild_permissions.administrator or \
                       interaction.user.guild_permissions.manage_guild or \
                       await perm_service.is_server_admin(interaction.user) or \
                       settings.is_bot_owner(interaction.user.id)
            if not is_admin:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لفتح لوحة التحكم!"),
                    ephemeral=True
                )
                return

        view = ControlMainView()
        embed = build_main_control_embed(interaction.guild, interaction.user)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

# --- VIEWS ---

class ControlMainView(ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @ui.button(label="⚡ اختصارات الأوامر", style=discord.ButtonStyle.primary, emoji="⚡", row=0)
    async def shortcuts_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        view = ShortcutsView()
        await interaction.edit_original_response(embed=view.get_embed(), view=view)

    @ui.button(label="🛡️ أنظمة الحماية (Security)", style=discord.ButtonStyle.secondary, emoji="🛡️", row=0)
    async def security_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        async with AsyncSessionLocal() as session:
            sec_service = SecurityService(session)
            sec_settings = await sec_service.get_security_settings(interaction.guild.id)
            view = SecurityControlView(sec_settings)
            embed = view.build_embed()
            await interaction.edit_original_response(embed=embed, view=view)

    @ui.button(label="🤖 الإشراف التلقائي (AutoMod)", style=discord.ButtonStyle.secondary, emoji="🤖", row=1)
    async def automod_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        async with AsyncSessionLocal() as session:
            am_service = AutoModService(session)
            am_settings = await am_service.get_automod_settings(interaction.guild.id)
            view = AutoModControlView(am_settings)
            embed = view.build_embed()
            await interaction.edit_original_response(embed=embed, view=view)

    @ui.button(label="📋 سجلات اللوجات (Logs)", style=discord.ButtonStyle.secondary, emoji="📋", row=1)
    async def logs_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            log_settings = await log_service.get_log_settings(interaction.guild.id)
            view = LogsControlView(log_settings)
            embed = view.build_embed()
            await interaction.edit_original_response(embed=embed, view=view)

    @ui.button(label="💰 نظام أروا والمتجر (Economy)", style=discord.ButtonStyle.secondary, emoji="✨", row=2)
    async def economy_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            shop_service = ShopService(session)
            count, total, avg = await eco_service.get_average(include_bank=True)
            products = await shop_service.list_products(enabled_only=True)
            view = EconomyControlView(count, total, len(products))
            embed = view.build_embed()
            await interaction.edit_original_response(embed=embed, view=view)

# --- SECURITY INTERACTIVE CONTROL VIEW ---

class SecurityControlView(ui.View):
    def __init__(self, sec_settings):
        super().__init__(timeout=300)
        self.sec_settings = sec_settings
        self.refresh_button_styles()

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🛡️ إعدادات الحماية المتقدمة (Security System)",
            description="اضغط على الأزرار أدناه لتفعيل أو تعطيل أي من أنظمة الحماية بشكل فوري ومباشر:",
            color=discord.Color.blue()
        )
        embed.add_field(name="🚫 Anti-Spam", value="مفعل ✅" if self.sec_settings.anti_spam_enabled else "معطل ❌", inline=True)
        embed.add_field(name="🚪 Anti-Raid", value="مفعل ✅" if self.sec_settings.anti_raid_enabled else "معطل ❌", inline=True)
        embed.add_field(name="💣 Anti-Nuke", value="مفعل ✅" if self.sec_settings.anti_nuke_enabled else "معطل ❌", inline=True)
        embed.add_field(name="🤖 Anti-Bot", value="مفعل ✅" if self.sec_settings.anti_bot_enabled else "معطل ❌", inline=True)
        embed.add_field(name="🔗 Anti-Invite", value="مفعل ✅" if self.sec_settings.anti_invite_enabled else "معطل ❌", inline=True)
        embed.add_field(name="🌐 Anti-Link", value="مفعل ✅" if self.sec_settings.anti_links_enabled else "معطل ❌", inline=True)
        embed.set_footer(text="التعديل يتم حفظه وتطبيقه فورياً في قاعدة البيانات")
        return embed

    def refresh_button_styles(self):
        self.toggle_spam_btn.style = discord.ButtonStyle.success if self.sec_settings.anti_spam_enabled else discord.ButtonStyle.secondary
        self.toggle_raid_btn.style = discord.ButtonStyle.success if self.sec_settings.anti_raid_enabled else discord.ButtonStyle.secondary
        self.toggle_nuke_btn.style = discord.ButtonStyle.success if self.sec_settings.anti_nuke_enabled else discord.ButtonStyle.secondary
        self.toggle_bot_btn.style = discord.ButtonStyle.success if self.sec_settings.anti_bot_enabled else discord.ButtonStyle.secondary
        self.toggle_inv_btn.style = discord.ButtonStyle.success if self.sec_settings.anti_invite_enabled else discord.ButtonStyle.secondary
        self.toggle_link_btn.style = discord.ButtonStyle.success if self.sec_settings.anti_links_enabled else discord.ButtonStyle.secondary

    async def toggle_feature(self, interaction: discord.Interaction, field_name: str):
        await interaction.response.defer()
        async with AsyncSessionLocal() as session:
            sec_service = SecurityService(session)
            current_val = getattr(self.sec_settings, field_name)
            new_val = not current_val
            await sec_service.update_security_settings(interaction.guild.id, **{field_name: new_val})
            self.sec_settings = await sec_service.get_security_settings(interaction.guild.id)
            self.refresh_button_styles()
            await interaction.edit_original_response(embed=self.build_embed(), view=self)

    @ui.button(label="Anti-Spam", emoji="🚫", row=0)
    async def toggle_spam_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_feature(interaction, "anti_spam_enabled")

    @ui.button(label="Anti-Raid", emoji="🚪", row=0)
    async def toggle_raid_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_feature(interaction, "anti_raid_enabled")

    @ui.button(label="Anti-Nuke", emoji="💣", row=0)
    async def toggle_nuke_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_feature(interaction, "anti_nuke_enabled")

    @ui.button(label="Anti-Bot", emoji="🤖", row=1)
    async def toggle_bot_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_feature(interaction, "anti_bot_enabled")

    @ui.button(label="Anti-Invite", emoji="🔗", row=1)
    async def toggle_inv_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_feature(interaction, "anti_invite_enabled")

    @ui.button(label="Anti-Links", emoji="🌐", row=1)
    async def toggle_link_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_feature(interaction, "anti_links_enabled")

    @ui.button(label="عودة للقائمة الرئيسية", style=discord.ButtonStyle.danger, emoji="⬅️", row=4)
    async def back_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        view = ControlMainView()
        embed = build_main_control_embed(interaction.guild, interaction.user)
        await interaction.edit_original_response(embed=embed, view=view)

# --- AUTOMOD INTERACTIVE CONTROL VIEW ---

class AutoModControlView(ui.View):
    def __init__(self, am_settings):
        super().__init__(timeout=300)
        self.am_settings = am_settings
        self.refresh_button_styles()

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🤖 نظام الإشراف التلقائي (AutoMod Control)",
            description="اضغط على الأزرار أدناه لتفعيل أو تعطيل أي من فلاتر الأوتومود فورياً:",
            color=discord.Color.dark_teal()
        )
        embed.add_field(name="🔗 فلتر الروابط (Links)", value="مفعل ✅" if self.am_settings.links_filter_enabled else "معطل ❌", inline=True)
        embed.add_field(name="🤬 فلتر الشتائم (Bad Words)", value="مفعل ✅" if self.am_settings.bad_words_filter_enabled else "معطل ❌", inline=True)
        embed.add_field(name="📢 فلتر المنشن (Mass Mention)", value="مفعل ✅" if self.am_settings.mass_mention_filter_enabled else "معطل ❌", inline=True)
        embed.add_field(name="🔠 فلتر الأحرف الكبيرة (Caps)", value="مفعل ✅" if self.am_settings.caps_filter_enabled else "معطل ❌", inline=True)
        embed.add_field(name="🔁 فلتر التكرار (Duplication)", value="مفعل ✅" if self.am_settings.spam_duplication_filter_enabled else "معطل ❌", inline=True)
        embed.set_footer(text="يتم تطبيق التعديلات التلقائية على الفور")
        return embed

    def refresh_button_styles(self):
        self.toggle_links_btn.style = discord.ButtonStyle.success if self.am_settings.links_filter_enabled else discord.ButtonStyle.secondary
        self.toggle_words_btn.style = discord.ButtonStyle.success if self.am_settings.bad_words_filter_enabled else discord.ButtonStyle.secondary
        self.toggle_mention_btn.style = discord.ButtonStyle.success if self.am_settings.mass_mention_filter_enabled else discord.ButtonStyle.secondary
        self.toggle_caps_btn.style = discord.ButtonStyle.success if self.am_settings.caps_filter_enabled else discord.ButtonStyle.secondary
        self.toggle_dup_btn.style = discord.ButtonStyle.success if self.am_settings.spam_duplication_filter_enabled else discord.ButtonStyle.secondary

    async def toggle_feature(self, interaction: discord.Interaction, field_name: str):
        await interaction.response.defer()
        async with AsyncSessionLocal() as session:
            am_service = AutoModService(session)
            current_val = getattr(self.am_settings, field_name)
            new_val = not current_val
            await am_service.update_automod_settings(interaction.guild.id, **{field_name: new_val})
            self.am_settings = await am_service.get_automod_settings(interaction.guild.id)
            self.refresh_button_styles()
            await interaction.edit_original_response(embed=self.build_embed(), view=self)

    @ui.button(label="فلتر الروابط", emoji="🔗", row=0)
    async def toggle_links_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_feature(interaction, "links_filter_enabled")

    @ui.button(label="فلتر الشتائم", emoji="🤬", row=0)
    async def toggle_words_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_feature(interaction, "bad_words_filter_enabled")

    @ui.button(label="فلتر المنشن", emoji="📢", row=0)
    async def toggle_mention_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_feature(interaction, "mass_mention_filter_enabled")

    @ui.button(label="فلتر الأحرف الكبيرة", emoji="🔠", row=1)
    async def toggle_caps_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_feature(interaction, "caps_filter_enabled")

    @ui.button(label="فلتر التكرار", emoji="🔁", row=1)
    async def toggle_dup_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_feature(interaction, "spam_duplication_filter_enabled")

    @ui.button(label="عودة للقائمة الرئيسية", style=discord.ButtonStyle.danger, emoji="⬅️", row=4)
    async def back_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        view = ControlMainView()
        embed = build_main_control_embed(interaction.guild, interaction.user)
        await interaction.edit_original_response(embed=embed, view=view)

# --- LOGS INTERACTIVE CONTROL VIEW ---

class LogsControlView(ui.View):
    def __init__(self, log_settings):
        super().__init__(timeout=300)
        self.log_settings = log_settings
        self.selected_category = "all"

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📋 نظام سجلات اللوجات المتقدم (Audit Logs)",
            description="حدد نوع السجل ثم اختر القناة من القائمة المنسدلة لتعيينها مباشرة:",
            color=discord.Color.purple()
        )
        def fmt_ch(chid):
            return f"<#{chid}>" if chid else "`غير مخصص`"
        embed.add_field(name="👥 سجل الأعضاء", value=fmt_ch(self.log_settings.member_logs_channel_id), inline=True)
        embed.add_field(name="💬 سجل الرسائل", value=fmt_ch(self.log_settings.message_logs_channel_id), inline=True)
        embed.add_field(name="🎙️ سجل الصوت", value=fmt_ch(self.log_settings.voice_logs_channel_id), inline=True)
        embed.add_field(name="🎭 سجل الرتب", value=fmt_ch(self.log_settings.role_logs_channel_id), inline=True)
        embed.add_field(name="📁 سجل القنوات", value=fmt_ch(self.log_settings.channel_logs_channel_id), inline=True)
        embed.add_field(name="🔨 سجل العقوبات", value=fmt_ch(self.log_settings.moderation_logs_channel_id), inline=True)
        embed.add_field(name="💰 سجل الاقتصاد", value=fmt_ch(self.log_settings.economy_logs_channel_id), inline=True)
        embed.add_field(name="🛡️ سجل الأمان", value=fmt_ch(self.log_settings.security_logs_channel_id), inline=True)
        return embed

    @ui.select(
        placeholder="اختر نوع السجل المراد تعيينه أو تغييره...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="👥 سجل الأعضاء (Member Logs)", value="member_logs_channel_id", emoji="👥"),
            discord.SelectOption(label="💬 سجل الرسائل (Message Logs)", value="message_logs_channel_id", emoji="💬"),
            discord.SelectOption(label="🎙️ سجل الرومات الصوتية (Voice Logs)", value="voice_logs_channel_id", emoji="🎙️"),
            discord.SelectOption(label="🎭 سجل الرتب والصلاحيات (Role Logs)", value="role_logs_channel_id", emoji="🎭"),
            discord.SelectOption(label="📁 سجل تعديل القنوات (Channel Logs)", value="channel_logs_channel_id", emoji="📁"),
            discord.SelectOption(label="🔨 سجل العقوبات والإشراف (Mod Logs)", value="moderation_logs_channel_id", emoji="🔨"),
            discord.SelectOption(label="💰 سجل الاقتصاد والمتجر (Economy Logs)", value="economy_logs_channel_id", emoji="💰"),
            discord.SelectOption(label="🛡️ سجل الأمان والحماية (Security Logs)", value="security_logs_channel_id", emoji="🛡️"),
            discord.SelectOption(label="🌐 تعيين كافة السجلات لقناة واحدة", value="all", emoji="🌐"),
        ],
        row=0
    )
    async def log_type_select(self, interaction: discord.Interaction, select: ui.Select):
        self.selected_category = select.values[0]
        await interaction.response.defer()

    @ui.select(cls=ui.ChannelSelect, placeholder="اختر القناة المخصصة للوج...", channel_types=[discord.ChannelType.text], row=1)
    async def channel_select(self, interaction: discord.Interaction, select: ui.ChannelSelect):
        channel = select.values[0]
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            if self.selected_category == "all":
                await log_service.update_log_settings(
                    interaction.guild.id,
                    member_logs_channel_id=channel.id,
                    message_logs_channel_id=channel.id,
                    voice_logs_channel_id=channel.id,
                    role_logs_channel_id=channel.id,
                    channel_logs_channel_id=channel.id,
                    moderation_logs_channel_id=channel.id,
                    economy_logs_channel_id=channel.id,
                    security_logs_channel_id=channel.id
                )
            else:
                await log_service.update_log_settings(interaction.guild.id, **{self.selected_category: channel.id})

            self.log_settings = await log_service.get_log_settings(interaction.guild.id)
            await interaction.edit_original_response(embed=self.build_embed(), view=self)

    @ui.button(label="مسح كافة قنوات اللوجات", style=discord.ButtonStyle.secondary, emoji="🗑️", row=2)
    async def clear_all_logs_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            await log_service.update_log_settings(
                interaction.guild.id,
                member_logs_channel_id=None,
                message_logs_channel_id=None,
                voice_logs_channel_id=None,
                role_logs_channel_id=None,
                channel_logs_channel_id=None,
                moderation_logs_channel_id=None,
                economy_logs_channel_id=None,
                security_logs_channel_id=None
            )
            self.log_settings = await log_service.get_log_settings(interaction.guild.id)
            await interaction.edit_original_response(embed=self.build_embed(), view=self)

    @ui.button(label="عودة للقائمة الرئيسية", style=discord.ButtonStyle.danger, emoji="⬅️", row=4)
    async def back_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        view = ControlMainView()
        embed = build_main_control_embed(interaction.guild, interaction.user)
        await interaction.edit_original_response(embed=embed, view=view)

# --- ECONOMY & SHOP INTERACTIVE CONTROL VIEW ---

class GiveAuraModal(ui.Modal, title="💰 إضافة رصيد أروا لعضو"):
    amount = ui.TextInput(label="المبلغ المراد إضافته", placeholder="1000", required=True)
    reason = ui.TextInput(label="السبب", placeholder="مكافأة نشاط", default="Control Panel Reward", required=False)

    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            val = int(self.amount.value.replace(",", ""))
            async with AsyncSessionLocal() as session:
                eco_service = EconomyService(session)
                wallet = await eco_service.add_balance(self.member.id, val, "WALLET", self.reason.value, actor_id=interaction.user.id)
                await interaction.followup.send(embed=EmbedBuilder.success("تمت الإضافة", f"تم إضافة **`{val:,}`** أروا لحساب {self.member.mention}.\nالرصيد الحالي: `{wallet.balance:,}`"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)

class EconomyControlView(ui.View):
    def __init__(self, accounts_count: int, total_wealth: int, products_count: int):
        super().__init__(timeout=300)
        self.accounts_count = accounts_count
        self.total_wealth = total_wealth
        self.products_count = products_count

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"✨ إدارة نظام أورا ({settings.CURRENCY_NAME}) والمتجر",
            description="تحكم شامل في السيولة النقدية، الحسابات، ومنتجات المتجر:",
            color=discord.Color.gold()
        )
        embed.add_field(name="🪙 اسم العملة", value=f"**{settings.CURRENCY_NAME}** {settings.CURRENCY_EMOJI}", inline=True)
        embed.add_field(name="👥 الحسابات المسجلة", value=f"`{self.accounts_count:,}` حساب", inline=True)
        embed.add_field(name="💰 إجمالي السيولة", value=f"`{self.total_wealth:,}` {settings.CURRENCY_NAME}", inline=True)
        embed.add_field(name="🛒 المنتجات المتاحة", value=f"`{self.products_count}` منتجات", inline=True)
        return embed

    @ui.button(label="إضافة رصيد لعضو", style=discord.ButtonStyle.success, emoji="➕", row=0)
    async def give_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد إضافة الرصيد له:", view=MemberSelectorView(action="give_aura"), embed=None)

    @ui.button(label="فتح متجر البانرات", style=discord.ButtonStyle.primary, emoji="🖼️", row=0)
    async def open_banner_shop_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            shop_service = ShopService(session)
            products = await shop_service.list_products(enabled_only=True)
            banners = [p for p in products if p.type in ["BANNER", "COSMETIC"]]
            if not banners:
                await interaction.followup.send("❌ لا توجد بانرات مسجلة في المتجر حالياً.", ephemeral=True)
                return
            carousel = BannerCarouselView(banners, interaction.user.id, 0)
            embed = await carousel.get_current_embed(interaction.user.id)
            await interaction.followup.send(embed=embed, view=carousel, ephemeral=True)

    @ui.button(label="عودة للقائمة الرئيسية", style=discord.ButtonStyle.danger, emoji="⬅️", row=4)
    async def back_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        view = ControlMainView()
        embed = build_main_control_embed(interaction.guild, interaction.user)
        await interaction.edit_original_response(embed=embed, view=view)

# --- SHORTCUTS & ACTION VIEWS ---

class ShortcutsView(ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    def get_embed(self):
        embed = discord.Embed(
            title="⚡ اختصارات الأوامر والكلمات المفتاحية التفاعلية",
            description=(
                "اختر الأمر المراد تنفيذه مباشرة أو يمكنك ببساطة كتابة أي من الكلمات المفتاحية في الشات:\n"
                "• **`تحذير`** ➔ فتح نافذة التحذير وإرفاق الدليل فورياً.\n"
                "• **`كتم`** أو **`عزل`** ➔ فتح نافذة العزل المؤقت مع المدة والدليل.\n"
                "• **`طرد`** أو **`حظر`** ➔ فتح نافذة الطرد/الحظر مع السبب والدليل.\n"
                "• **`مسح`** ➔ فتح نافذة مسح الرسائل.\n"
                "• **`قفل`** أو **`فتح`** ➔ قفل أو فتح القناة فورياً.\n"
                "• **`بروفايل`** أو **`رصيد`** أو **`متجر`** ➔ فتح بطاقة الحساب أو متجر البانرات."
            ),
            color=discord.Color.blue()
        )
        return embed

    @ui.button(label="عودة", style=discord.ButtonStyle.danger, emoji="⬅️", row=4)
    async def back_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        view = ControlMainView()
        embed = build_main_control_embed(interaction.guild, interaction.user)
        await interaction.edit_original_response(embed=embed, view=view)

    # Moderation Shortcuts
    @ui.button(label="Warn (تحذير)", style=discord.ButtonStyle.secondary, emoji="⚠️", row=0)
    async def warn_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد تحذيره:", view=MemberSelectorView(action="warn"), embed=None)

    @ui.button(label="Timeout (عزل)", style=discord.ButtonStyle.secondary, emoji="⏱️", row=0)
    async def timeout_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد عزله (Timeout):", view=MemberSelectorView(action="timeout"), embed=None)

    @ui.button(label="Kick (طرد)", style=discord.ButtonStyle.secondary, emoji="👢", row=0)
    async def kick_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد طرده:", view=MemberSelectorView(action="kick"), embed=None)

    @ui.button(label="Ban (حظر)", style=discord.ButtonStyle.secondary, emoji="🔨", row=0)
    async def ban_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد حظره:", view=MemberSelectorView(action="ban"), embed=None)

    @ui.button(label="Purge (مسح)", style=discord.ButtonStyle.secondary, emoji="🧹", row=1)
    async def purge_btn(self, interaction: discord.Interaction, button: ui.Button):
        from bot.cogs.shortcuts import ShortcutPurgeModal
        await interaction.response.send_modal(ShortcutPurgeModal())

    @ui.button(label="Lock (قفل)", style=discord.ButtonStyle.secondary, emoji="🔒", row=1)
    async def lock_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر القناة المراد قفلها:", view=ChannelSelectorView(action="lock"), embed=None)

    @ui.button(label="Unlock (فتح)", style=discord.ButtonStyle.secondary, emoji="🔓", row=1)
    async def unlock_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر القناة المراد فتحها:", view=ChannelSelectorView(action="unlock"), embed=None)

    # Voice Management
    @ui.button(label="Move Member", style=discord.ButtonStyle.secondary, emoji="🎙️", row=2)
    async def move_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد نقله:", view=MemberSelectorView(action="move"), embed=None)

    @ui.button(label="Voice Mute", style=discord.ButtonStyle.secondary, emoji="🔇", row=2)
    async def v_mute_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد كتم صوته:", view=MemberSelectorView(action="voice_mute"), embed=None)

    @ui.button(label="Disconnect", style=discord.ButtonStyle.secondary, emoji="🔌", row=2)
    async def v_disc_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد فصله من الصوت:", view=MemberSelectorView(action="voice_disconnect"), embed=None)

# --- SELECTORS ---

class MemberSelectorView(ui.View):
    def __init__(self, action: str):
        super().__init__(timeout=180)
        self.action = action

    @ui.select(cls=ui.UserSelect, placeholder="اختر العضو...", min_values=1, max_values=1)
    async def select_member(self, interaction: discord.Interaction, select: ui.UserSelect):
        member = select.values[0]
        if not isinstance(member, discord.Member):
            member = interaction.guild.get_member(member.id)
            if not member:
                await interaction.response.send_message("يجب اختيار عضو متواجد في السيرفر!", ephemeral=True)
                return

        from bot.cogs.shortcuts import ShortcutWarnModal, ShortcutTimeoutModal, ShortcutKickModal, ShortcutBanModal, ShortcutDeleteWarnModal
        if self.action == "warn":
            await interaction.response.send_modal(ShortcutWarnModal(member))
        elif self.action == "timeout":
            await interaction.response.send_modal(ShortcutTimeoutModal(member))
        elif self.action == "untimeout":
            await interaction.response.defer(ephemeral=True)
            try:
                await member.timeout(None, reason=f"فك التايم أوت بواسطة لوحة التحكم | المشرف: {interaction.user}")
                await interaction.followup.send(f"✅ تم فك التايم أوت عن {member.mention} بنجاح.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ فشل فك التايم: {e}", ephemeral=True)
        elif self.action == "delete_warn":
            await interaction.response.send_modal(ShortcutDeleteWarnModal(member))
        elif self.action in ["warnings", "warns"]:
            await interaction.response.defer(ephemeral=True)
            async with AsyncSessionLocal() as session:
                service = WarningService(session)
                warnings_list = await service.get_warnings(interaction.guild.id, member.id)
                if not warnings_list:
                    await interaction.followup.send(f"✅ لا توجد أي تحذيرات مسجلة للعضو {member.mention}.", ephemeral=True)
                    return
                status_badges = {"ACTIVE": "🟢 نشط", "EXPIRED": "⚪ منتهي", "REMOVED": "🔴 محذوف", "VOIDED": "🟡 ملغى"}
                embed = discord.Embed(title=f"📋 سجل تحذيرات | {member.display_name}", color=discord.Color.blue(), timestamp=discord.utils.utcnow())
                embed.set_thumbnail(url=member.display_avatar.url)
                for w in warnings_list[:10]:
                    mod = interaction.guild.get_member(w.moderator_id)
                    mod_str = mod.mention if mod else f"`{w.moderator_id}`"
                    status_str = status_badges.get(w.status, w.status)
                    type_str = "رسمي" if w.warning_type == "formal" else "شفهي"
                    exp_str = f"<t:{int(w.expires_at.timestamp())}:R>" if w.expires_at else "دائم"
                    embed.add_field(name=f"#{w.local_id} | ({type_str}) - {status_str}", value=f"**السبب:** {w.reason}\n**المشرف:** {mod_str}\n**الانتهاء:** {exp_str}\n**التاريخ:** <t:{int(w.created_at.timestamp())}:D>", inline=False)
                embed.set_footer(text=f"إجمالي التحذيرات: {len(warnings_list)}")
                await interaction.followup.send(embed=embed, ephemeral=True)
        elif self.action == "kick":
            await interaction.response.send_modal(ShortcutKickModal(member))
        elif self.action == "ban":
            await interaction.response.send_modal(ShortcutBanModal(member))
        elif self.action in ["balance", "bal"]:
            await interaction.response.defer(ephemeral=True)
            async with AsyncSessionLocal() as session:
                eco_service = EconomyService(session)
                bal, bank_bal, total = await eco_service.get_balance(member.id)
                embed = discord.Embed(
                    title=f"💰 تفاصيل الرصيد | {member.display_name}",
                    description=(
                        f"• 💵 **المحفظة:** `{bal:,}` {settings.CURRENCY_EMOJI}\n"
                        f"• 🏦 **البنك:** `{bank_bal:,}` {settings.CURRENCY_EMOJI}\n"
                        f"• ✨ **الإجمالي:** **`{total:,}` {settings.CURRENCY_NAME}**"
                    ),
                    color=discord.Color.gold(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await interaction.followup.send(embed=embed, ephemeral=True)
        elif self.action == "give_aura":
            await interaction.response.send_modal(GiveAuraModal(member))
        elif self.action == "move":
            view = ChannelSelectorView(action="move_target", member=member)
            await interaction.response.edit_message(content=f"اختر القناة التي تريد نقل {member.mention} إليها:", view=view)
        elif self.action == "voice_mute":
            await interaction.response.defer(ephemeral=True)
            async with AsyncSessionLocal() as session:
                service = VoiceService(session)
                count, errs = await service.set_mute_state(interaction.guild, interaction.user, True, member=member, reason="CP Mute")
                if count > 0: await interaction.followup.send(f"✅ تم كتم صوت {member.mention}.", ephemeral=True)
                else: await interaction.followup.send(f"❌ فشل: {', '.join(errs)}", ephemeral=True)
        elif self.action == "voice_unmute":
            await interaction.response.defer(ephemeral=True)
            async with AsyncSessionLocal() as session:
                service = VoiceService(session)
                count, errs = await service.set_mute_state(interaction.guild, interaction.user, False, member=member, reason="CP Unmute")
                if count > 0: await interaction.followup.send(f"✅ تم فك كتم صوت {member.mention}.", ephemeral=True)
                else: await interaction.followup.send(f"❌ فشل: {', '.join(errs)}", ephemeral=True)
        elif self.action == "voice_disconnect":
            await interaction.response.defer(ephemeral=True)
            async with AsyncSessionLocal() as session:
                service = VoiceService(session)
                count, errs = await service.disconnect_members(interaction.guild, interaction.user, member=member, reason="CP Disconnect")
                if count > 0: await interaction.followup.send(f"✅ تم فصل {member.mention}.", ephemeral=True)
                else: await interaction.followup.send(f"❌ فشل: {', '.join(errs)}", ephemeral=True)

class ChannelSelectorView(ui.View):
    def __init__(self, action: str, member: Optional[discord.Member] = None):
        super().__init__(timeout=180)
        self.action = action
        self.member = member

    @ui.select(cls=ui.ChannelSelect, placeholder="اختر القناة...", channel_types=[discord.ChannelType.text, discord.ChannelType.voice])
    async def select_channel(self, interaction: discord.Interaction, select: ui.ChannelSelect):
        channel = select.values[0]
        
        if self.action == "lock":
            await self.execute_lock(interaction, channel)
        elif self.action == "unlock":
            await self.execute_unlock(interaction, channel)
        elif self.action == "move_target":
            await self.execute_move(interaction, self.member, channel)

    async def execute_lock(self, interaction: discord.Interaction, channel: Union[discord.TextChannel, discord.VoiceChannel]):
        await interaction.response.defer(ephemeral=True)
        if isinstance(channel, discord.VoiceChannel):
            async with AsyncSessionLocal() as session:
                service = VoiceService(session)
                success = await service.lock_channel(interaction.guild, interaction.user, channel, reason="Locked via CP")
                if success: await interaction.followup.send(f"✅ تم قفل القناة الصوتية {channel.mention}.")
                else: await interaction.followup.send("❌ فشل القفل.")
        else:
            overwrite = channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason="Locked via Control Panel")
            await interaction.followup.send(f"✅ تم قفل القناة النصية {channel.mention}.")

    async def execute_unlock(self, interaction: discord.Interaction, channel: Union[discord.TextChannel, discord.VoiceChannel]):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            if isinstance(channel, discord.VoiceChannel):
                service = VoiceService(session)
                success = await service.unlock_channel(interaction.guild, interaction.user, channel)
                if success: await interaction.followup.send(f"✅ تم فتح القناة الصوتية {channel.mention} بنجاح.")
                else: await interaction.followup.send("❌ فشل فتح القناة الصوتية.")
            else:
                overwrite = channel.overwrites_for(interaction.guild.default_role)
                overwrite.send_messages = None
                await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason="Unlocked via Control Panel")
                await interaction.followup.send(f"✅ تم فتح القناة النصية {channel.mention} بنجاح.")

    async def execute_move(self, interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            service = VoiceService(session)
            count, errors = await service.move_members(interaction.guild, interaction.user, channel, member=member)
            if count > 0:
                await interaction.followup.send(f"✅ تم نقل {member.mention} إلى {channel.mention} بنجاح.")
            else:
                await interaction.followup.send(f"❌ فشل النقل: {', '.join(errors)}")

async def setup(bot: commands.Bot):
    await bot.add_cog(ControlCog(bot))
