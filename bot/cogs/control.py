import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import Optional, List, Union
from datetime import timedelta

from bot.database.connection import AsyncSessionLocal
from bot.services.moderation_service import ModerationService
from bot.services.warning_service import WarningService
from bot.services.voice_service import VoiceService
from bot.services.permission_service import PermissionService
from bot.utils.embeds import EmbedBuilder
from bot.utils.audit_logs import format_id
from bot.utils.permissions import check_hierarchy

class ControlCog(commands.Cog):
    """Cog providing a Discord-based Control Panel for server management."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="control", description="فتح لوحة التحكم الإدارية للسيرفر")
    async def control_panel(self, interaction: discord.Interaction):
        """Main entry point for the Discord Control Panel."""
        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            # Basic check: user must have some administrative or moderation capability
            if not interaction.user.guild_permissions.administrator and \
               not interaction.user.guild_permissions.manage_guild and \
               not interaction.user.guild_permissions.moderate_members:
                await interaction.response.send_message(
                    embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لفتح لوحة التحكم!"),
                    ephemeral=True
                )
                return

        view = ControlMainView()
        embed = discord.Embed(
            title="🛡️ لوحة التحكم الإدارية | Security Bot Hub",
            description=(
                "مرحباً بك في لوحة التحكم التفاعلية. يمكنك من خلال الأزرار أدناه "
                "إدارة إعدادات السيرفر، تنفيذ الاختصارات الإدارية، والتحكم في أنظمة الحماية."
            ),
            color=discord.Color.from_rgb(88, 101, 242)
        )
        embed.add_field(name="🌐 السيرفر", value=f"**{interaction.guild.name}**", inline=True)
        embed.add_field(name="👮 المشرف", value=interaction.user.mention, inline=True)
        embed.set_footer(text="استخدم القوائم أدناه للتنقل بين الأقسام")
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# --- VIEWS ---

class ControlMainView(ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @ui.button(label="⚡ اختصارات الأوامر", style=discord.ButtonStyle.primary, emoji="⚡", row=0)
    async def shortcuts_btn(self, interaction: discord.Interaction, button: ui.Button):
        view = ShortcutsView()
        await interaction.response.edit_message(
            embed=view.get_embed(),
            view=view
        )

    @ui.button(label="🛡️ Security", style=discord.ButtonStyle.secondary, emoji="🛡️", row=0)
    async def security_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("سيتم إضافة قسم الحماية قريباً...", ephemeral=True)

    @ui.button(label="🤖 AutoMod", style=discord.ButtonStyle.secondary, emoji="🤖", row=1)
    async def automod_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("سيتم إضافة قسم الأوتومود قريباً...", ephemeral=True)

    @ui.button(label="📋 Logs", style=discord.ButtonStyle.secondary, emoji="📋", row=1)
    async def logs_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("سيتم إضافة قسم اللوجات قريباً...", ephemeral=True)

    @ui.button(label="💰 Economy", style=discord.ButtonStyle.secondary, emoji="💰", row=2)
    async def economy_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("سيتم إضافة قسم الاقتصاد قريباً...", ephemeral=True)

    @ui.button(label="⚙️ Server Settings", style=discord.ButtonStyle.secondary, emoji="⚙️", row=2)
    async def settings_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("سيتم إضافة إعدادات السيرفر قريباً...", ephemeral=True)

class ShortcutsView(ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    def get_embed(self):
        embed = discord.Embed(
            title="⚡ اختصارات الأوامر الإدارية",
            description=(
                "اختر الأمر المراد تنفيذه من القائمة أدناه. سيتم طلب العضو أو التفاصيل "
                "بشكل تفاعلي بعد اختيارك."
            ),
            color=discord.Color.blue()
        )
        return embed

    @ui.button(label="عودة", style=discord.ButtonStyle.danger, emoji="⬅️", row=4)
    async def back_btn(self, interaction: discord.Interaction, button: ui.Button):
        from bot.cogs.control import ControlMainView
        view = ControlMainView()
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🛡️ لوحة التحكم الإدارية | Security Bot Hub",
                description="مرحباً بك مجدداً في اللوحة الرئيسية.",
                color=discord.Color.from_rgb(88, 101, 242)
            ),
            view=view
        )

    # Moderation Shortcuts
    @ui.button(label="Warn", style=discord.ButtonStyle.secondary, emoji="⚠️", row=0)
    async def warn_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد تحذيره:", view=MemberSelectorView(action="warn"), embed=None)

    @ui.button(label="Timeout", style=discord.ButtonStyle.secondary, emoji="⏱️", row=0)
    async def timeout_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد عزله (Timeout):", view=MemberSelectorView(action="timeout"), embed=None)

    @ui.button(label="Kick", style=discord.ButtonStyle.secondary, emoji="👢", row=0)
    async def kick_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد طرده:", view=MemberSelectorView(action="kick"), embed=None)

    @ui.button(label="Ban", style=discord.ButtonStyle.secondary, emoji="🔨", row=0)
    async def ban_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد حظره:", view=MemberSelectorView(action="ban"), embed=None)

    @ui.button(label="Purge", style=discord.ButtonStyle.secondary, emoji="🧹", row=1)
    async def purge_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(PurgeModal())

    @ui.button(label="Lock", style=discord.ButtonStyle.secondary, emoji="🔒", row=1)
    async def lock_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر القناة المراد قفلها:", view=ChannelSelectorView(action="lock"), embed=None)

    @ui.button(label="Unlock", style=discord.ButtonStyle.secondary, emoji="🔓", row=1)
    async def unlock_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر القناة المراد فتحها:", view=ChannelSelectorView(action="unlock"), embed=None)

    # Voice Management
    @ui.button(label="Move Member", style=discord.ButtonStyle.secondary, emoji="🎙️", row=2)
    async def move_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد نقله:", view=MemberSelectorView(action="move"), embed=None)

    @ui.button(label="Voice Mute", style=discord.ButtonStyle.secondary, emoji="🔇", row=2)
    async def v_mute_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="اختر العضو المراد كتم صوته:", view=MemberSelectorView(action="voice_mute"), embed=None)

    @ui.button(label="Disconnect", style=discord.ButtonStyle.secondary, emoji="👢", row=2)
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
            await interaction.response.send_message("يجب اختيار عضو متواجد في السيرفر!", ephemeral=True)
            return

        if self.action == "warn":
            await interaction.response.send_modal(WarnModal(member))
        elif self.action == "timeout":
            await interaction.response.send_modal(TimeoutModal(member))
        elif self.action == "kick":
            await interaction.response.send_modal(KickModal(member))
        elif self.action == "ban":
            await interaction.response.send_modal(BanModal(member))
        elif self.action == "move":
            view = ChannelSelectorView(action="move_target", member=member)
            await interaction.response.edit_message(content=f"اختر القناة التي تريد نقل {member.mention} إليها:", view=view)
        elif self.action == "voice_mute":
            await interaction.response.send_modal(VoiceMuteModal(member))
        elif self.action == "voice_disconnect":
            await interaction.response.send_modal(VoiceDisconnectModal(member))

class ChannelSelectorView(ui.View):
    def __init__(self, action: str, member: Optional[discord.Member] = None):
        super().__init__(timeout=180)
        self.action = action
        self.member = member

    @ui.select(cls=ui.ChannelSelect, placeholder="اختر القناة...", channel_types=[discord.ChannelType.text, discord.ChannelType.voice])
    async def select_channel(self, interaction: discord.Interaction, select: ui.ChannelSelect):
        channel = select.values[0]
        
        if self.action == "lock":
            await interaction.response.send_modal(LockModal(channel))
        elif self.action == "unlock":
            await self.execute_unlock(interaction, channel)
        elif self.action == "move_target":
            await self.execute_move(interaction, self.member, channel)

    async def execute_unlock(self, interaction: discord.Interaction, channel: Union[discord.TextChannel, discord.VoiceChannel]):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            if isinstance(channel, discord.VoiceChannel):
                service = VoiceService(session)
                success = await service.unlock_channel(interaction.guild, interaction.user, channel)
                if success:
                    await interaction.followup.send(f"✅ تم فتح القناة الصوتية {channel.mention} بنجاح.")
                else:
                    await interaction.followup.send("❌ فشل فتح القناة الصوتية.")
            else:
                # Text Channel Unlock
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

# --- MODALS ---

class WarnModal(ui.Modal, title="⚠️ تحذير عضو"):
    reason = ui.TextInput(label="السبب", placeholder="اكتب سبب التحذير هنا...", required=True, min_length=3)
    warn_type = ui.TextInput(label="النوع (شفهي / رسمي)", placeholder="اكتب 'verbal' للشفهي أو 'formal' للرسمي", default="formal", required=True)

    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            w_type = "verbal" if self.warn_type.value.lower() in ["شفهي", "verbal", "كلمة"] else "formal"
            warning, pun_msg = await service.issue_warning(
                interaction.guild, interaction.user, self.member, self.reason.value, warning_type=w_type
            )
            msg = f"✅ تم تحذير {self.member.mention} بنجاح. معرف التحذير: `{warning.local_id}`"
            if pun_msg: msg += f"\n{pun_msg}"
            await interaction.followup.send(msg)

class TimeoutModal(ui.Modal, title="⏱️ عزل مؤقت (Timeout)"):
    duration = ui.TextInput(label="المدة (مثال: 10m, 1h, 1d)", placeholder="10m", required=True)
    reason = ui.TextInput(label="السبب", placeholder="اكتب السبب هنا...", required=True)

    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        from bot.cogs.moderation import parse_duration
        seconds = parse_duration(self.duration.value)
        if not seconds:
            await interaction.followup.send("❌ صيغة مدة غير صحيحة! (مثال: 10m, 1h)")
            return

        async with AsyncSessionLocal() as session:
            service = ModerationService(session)
            success, msg = await service.timeout_user(interaction.guild, interaction.user, self.member, seconds, self.reason.value)
            if success: await interaction.followup.send(f"✅ {msg}")
            else: await interaction.followup.send(f"❌ {msg}")

class KickModal(ui.Modal, title="👢 طرد عضو"):
    reason = ui.TextInput(label="السبب", placeholder="اكتب السبب هنا...", required=True)

    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            service = ModerationService(session)
            success, msg = await service.kick_user(interaction.guild, interaction.user, self.member, self.reason.value)
            if success: await interaction.followup.send(f"✅ {msg}")
            else: await interaction.followup.send(f"❌ {msg}")

class BanModal(ui.Modal, title="🔨 حظر عضو"):
    reason = ui.TextInput(label="السبب", placeholder="اكتب السبب هنا...", required=True)
    delete_days = ui.TextInput(label="أيام مسح الرسائل (0-7)", default="0", required=True)

    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            days = int(self.delete_days.value) if self.delete_days.value.isdigit() else 0
            async with AsyncSessionLocal() as session:
                service = ModerationService(session)
                success, msg = await service.ban_user(interaction.guild, interaction.user, self.member, self.reason.value, delete_days=days)
                if success: await interaction.followup.send(f"✅ {msg}")
                else: await interaction.followup.send(f"❌ {msg}")
        except Exception as e:
            await interaction.followup.send(f"❌ فشل التنفيذ: {e}")

class PurgeModal(ui.Modal, title="🧹 مسح الرسائل"):
    amount = ui.TextInput(label="العدد (1-100)", placeholder="10", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            num = int(self.amount.value)
            deleted = await interaction.channel.purge(limit=num)
            await interaction.followup.send(f"✅ تم مسح {len(deleted)} رسالة بنجاح.")
        except Exception as e:
            await interaction.followup.send(f"❌ فشل المسح: {e}")

class LockModal(ui.Modal, title="🔒 قفل القناة"):
    reason = ui.TextInput(label="السبب", placeholder="Locked via CP", required=False)

    def __init__(self, channel: Union[discord.TextChannel, discord.VoiceChannel]):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        reason = self.reason.value or "Locked via Control Panel"
        
        if isinstance(self.channel, discord.VoiceChannel):
            async with AsyncSessionLocal() as session:
                service = VoiceService(session)
                success = await service.lock_channel(interaction.guild, interaction.user, self.channel, reason=reason)
                if success: await interaction.followup.send(f"✅ تم قفل القناة الصوتية {self.channel.mention}.")
                else: await interaction.followup.send("❌ فشل القفل.")
        else:
            overwrite = self.channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = False
            await self.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason=reason)
            await interaction.followup.send(f"✅ تم قفل القناة النصية {self.channel.mention}.")

class VoiceMuteModal(ui.Modal, title="🔇 كتم صوت"):
    mute = ui.TextInput(label="الحالة (true للكاتم / false للإلغاء)", default="true", required=True)
    reason = ui.TextInput(label="السبب", placeholder="Spamming", required=True)

    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        is_mute = self.mute.value.lower() == "true"
        async with AsyncSessionLocal() as session:
            service = VoiceService(session)
            count, errors = await service.set_mute_state(interaction.guild, interaction.user, is_mute, member=self.member, reason=self.reason.value)
            if count > 0: await interaction.followup.send(f"✅ تم {'كتم' if is_mute else 'إلغاء كتم'} صوت {self.member.mention}.")
            else: await interaction.followup.send(f"❌ فشل: {', '.join(errors)}")

class VoiceDisconnectModal(ui.Modal, title="👢 فصل من الصوت"):
    reason = ui.TextInput(label="السبب", placeholder="AFK", required=True)

    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            service = VoiceService(session)
            count, errors = await service.disconnect_members(interaction.guild, interaction.user, member=self.member, reason=self.reason.value)
            if count > 0: await interaction.followup.send(f"✅ تم فصل {self.member.mention} من القناة الصوتية.")
            else: await interaction.followup.send(f"❌ فشل: {', '.join(errors)}")

async def setup(bot: commands.Bot):
    await bot.add_cog(ControlCog(bot))
