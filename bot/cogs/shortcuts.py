import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import Optional, List, Union
from datetime import timedelta

from bot.config.settings import settings
from bot.database.connection import AsyncSessionLocal
from bot.database.repositories.shortcut_repository import ShortcutRepository, DEFAULT_SHORTCUTS
from bot.services.moderation_service import ModerationService
from bot.services.warning_service import WarningService
from bot.services.voice_service import VoiceService
from bot.services.permission_service import PermissionService
from bot.services.economy_service import EconomyService
from bot.services.profile_service import ProfileService
from bot.services.shop_service import ShopService
from bot.services.log_service import LogService
from bot.utils.embeds import EmbedBuilder
from bot.cogs.profile import ProfileView, BannerCarouselView

# --- SHORTCUT MODALS & VIEWS WITH PROOF / EVIDENCE SUPPORT ---

class ShortcutWarnModal(ui.Modal, title="⚠️ إصدار تحذير (مع الدليل)"):
    reason = ui.TextInput(label="سبب التحذير", placeholder="اكتب سبب التحذير هنا...", required=True, min_length=3)
    proof_url = ui.TextInput(label="رابط الدليل / صورة الإثبات (Proof URL)", placeholder="https://cdn.discordapp.com/...", required=False)
    warn_type = ui.TextInput(label="نوع التحذير (formal أو verbal)", default="formal", required=True)

    def __init__(self, target_member: discord.Member):
        super().__init__()
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            w_type = "verbal" if self.warn_type.value.lower() in ["verbal", "شفهي", "كلمة"] else "formal"
            evidence = [self.proof_url.value.strip()] if self.proof_url.value and self.proof_url.value.strip() else []
            
            warning, pun_msg = await service.issue_warning(
                interaction.guild,
                interaction.user,
                self.target_member,
                self.reason.value,
                warning_type=w_type,
                evidence_urls=evidence
            )

            msg = f"✅ تم إصدار تحذير لـ {self.target_member.mention} بنجاح!\n• **معرف التحذير:** `{warning.local_id}`\n• **السبب:** {self.reason.value}"
            if evidence:
                msg += f"\n• **الدليل:** {evidence[0]}"
            if pun_msg:
                msg += f"\n{pun_msg}"

            await interaction.followup.send(embed=EmbedBuilder.success("تم التحذير بنجاح", msg), ephemeral=True)

class ShortcutTimeoutModal(ui.Modal, title="⏱️ عزل مؤقت (Timeout) مع الدليل"):
    duration = ui.TextInput(label="المدة (مثال: 10m, 1h, 1d)", placeholder="10m", required=True)
    reason = ui.TextInput(label="السبب", placeholder="اكتب سبب العزل هنا...", required=True)
    proof_url = ui.TextInput(label="رابط الدليل (اختياري)", placeholder="https://...", required=False)

    def __init__(self, target_member: discord.Member):
        super().__init__()
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        from bot.cogs.moderation import parse_duration
        seconds = parse_duration(self.duration.value)
        if not seconds:
            await interaction.followup.send(embed=EmbedBuilder.error("خطأ", "صيغة مدة غير صحيحة! (مثال: 10m, 1h, 1d)"), ephemeral=True)
            return

        reason_full = self.reason.value
        if self.proof_url.value and self.proof_url.value.strip():
            reason_full += f" | Proof: {self.proof_url.value.strip()}"

        async with AsyncSessionLocal() as session:
            service = ModerationService(session)
            success, msg = await service.timeout_user(
                interaction.guild, interaction.user, self.target_member, seconds, reason_full
            )
            if success:
                await interaction.followup.send(embed=EmbedBuilder.success("تم العزل", msg), ephemeral=True)
            else:
                await interaction.followup.send(embed=EmbedBuilder.error("فشل", msg), ephemeral=True)

class ShortcutKickModal(ui.Modal, title="👢 طرد عضو مع الدليل"):
    reason = ui.TextInput(label="سبب الطرد", placeholder="اكتب سبب الطرد...", required=True)
    proof_url = ui.TextInput(label="رابط الدليل (اختياري)", placeholder="https://...", required=False)

    def __init__(self, target_member: discord.Member):
        super().__init__()
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        reason_full = self.reason.value
        if self.proof_url.value and self.proof_url.value.strip():
            reason_full += f" | Proof: {self.proof_url.value.strip()}"

        async with AsyncSessionLocal() as session:
            service = ModerationService(session)
            success, msg = await service.kick_user(
                interaction.guild, interaction.user, self.target_member, reason_full
            )
            if success:
                await interaction.followup.send(embed=EmbedBuilder.success("تم الطرد", msg), ephemeral=True)
            else:
                await interaction.followup.send(embed=EmbedBuilder.error("فشل", msg), ephemeral=True)

class ShortcutBanModal(ui.Modal, title="🔨 حظر عضو مع الدليل"):
    reason = ui.TextInput(label="سبب الحظر", placeholder="اكتب سبب الحظر...", required=True)
    delete_days = ui.TextInput(label="أيام مسح الرسائل (0-7)", default="0", required=True)
    proof_url = ui.TextInput(label="رابط الدليل (اختياري)", placeholder="https://...", required=False)

    def __init__(self, target_member: discord.Member):
        super().__init__()
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        reason_full = self.reason.value
        if self.proof_url.value and self.proof_url.value.strip():
            reason_full += f" | Proof: {self.proof_url.value.strip()}"

        days = int(self.delete_days.value) if self.delete_days.value.isdigit() else 0

        async with AsyncSessionLocal() as session:
            service = ModerationService(session)
            success, msg = await service.ban_user(
                interaction.guild, interaction.user, self.target_member, reason_full, delete_days=days
            )
            if success:
                await interaction.followup.send(embed=EmbedBuilder.success("تم الحظر", msg), ephemeral=True)
            else:
                await interaction.followup.send(embed=EmbedBuilder.error("فشل", msg), ephemeral=True)

class ShortcutPurgeModal(ui.Modal, title="🧹 مسح الرسائل"):
    amount = ui.TextInput(label="عدد الرسائل المراد مسحها (1-100)", placeholder="10", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            num = int(self.amount.value)
            if not 1 <= num <= 100:
                await interaction.followup.send("❌ يرجى إدخال رقم بين 1 و 100.", ephemeral=True)
                return
            deleted = await interaction.channel.purge(limit=num)
            await interaction.followup.send(embed=EmbedBuilder.success("تم المسح", f"تم مسح **{len(deleted)}** رسالة بنجاح."), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("خطأ", f"فشل المسح: {e}"), ephemeral=True)

class ShortcutDeleteWarnModal(ui.Modal, title="🗑️ حذف تحذير معين"):
    warning_id = ui.TextInput(label="رقم التحذير (ID)", placeholder="مثال: 1 أو 2 أو 3", required=True)
    reason = ui.TextInput(label="سبب الحذف / الإلغاء", placeholder="اكتب سبب حذف التحذير...", default="حذف عبر اختصار الأوامر", required=False)

    def __init__(self, target_member: discord.Member):
        super().__init__()
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            local_id = int(self.warning_id.value.strip())
        except ValueError:
            await interaction.followup.send("❌ يرجى كتابة رقم تحذير صحيح.", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            removed = await service.remove_warning(
                guild_id=interaction.guild.id,
                user_id=self.target_member.id,
                local_id=local_id,
                remover_id=interaction.user.id,
                reason=self.reason.value or "حذف عبر اختصار الأوامر"
            )
            if removed:
                await interaction.followup.send(
                    embed=EmbedBuilder.success(
                        "تم حذف التحذير",
                        f"✅ تم بنجاح حذف التحذير رقم **`#{local_id}`** للعضو {self.target_member.mention}."
                    ),
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    embed=EmbedBuilder.error(
                        "غير موجود",
                        f"❌ لم يتم العثور على تحذير بالرقم **`#{local_id}`** للعضو {self.target_member.mention}."
                    ),
                    ephemeral=True
                )

class ShortcutMoveVoiceChannelView(ui.View):
    """View to select target voice channel for moving member."""
    def __init__(self, target_member: discord.Member, author: discord.Member):
        super().__init__(timeout=90)
        self.target_member = target_member
        self.author = author

    @ui.select(cls=ui.ChannelSelect, placeholder="اختر الروم الصوتي المراد نقل العضو إليه...", channel_types=[discord.ChannelType.voice])
    async def select_voice_channel(self, interaction: discord.Interaction, select: ui.ChannelSelect):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ هذا الخيار مخصص لمن طلب الاختصار!", ephemeral=True)
            return

        target_channel = select.values[0]
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            service = VoiceService(session)
            count, errs = await service.move_members(
                interaction.guild, interaction.user, target_channel, member=self.target_member, reason="Shortcut Voice Move"
            )
            if count > 0:
                await interaction.followup.send(f"✅ تم نقل {self.target_member.mention} إلى الروم الصوتي {target_channel.mention} بنجاح.", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ فشل النقل: {', '.join(errs)}", ephemeral=True)

class ShortcutActionMemberSelectView(ui.View):
    """View to select the target member when an action shortcut trigger is fired."""
    def __init__(self, action: str, author: discord.Member):
        super().__init__(timeout=90)
        self.action = action
        self.author = author

    @ui.select(cls=ui.UserSelect, placeholder="اختر العضو المستهدف بالضغط هنا...", min_values=1, max_values=1)
    async def select_member(self, interaction: discord.Interaction, select: ui.UserSelect):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ هذا الخيار مخصص لمن قام بكتابة الاختصار!", ephemeral=True)
            return

        member = select.values[0]
        if not isinstance(member, discord.Member):
            member = interaction.guild.get_member(member.id)
            if not member:
                await interaction.response.send_message("❌ العضو غير موجود في السيرفر!", ephemeral=True)
                return

        if self.action == "warn":
            await interaction.response.send_modal(ShortcutWarnModal(member))
        elif self.action == "timeout":
            await interaction.response.send_modal(ShortcutTimeoutModal(member))
        elif self.action == "untimeout":
            await interaction.response.defer(ephemeral=True)
            try:
                await member.timeout(None, reason=f"فك التايم أوت بواسطة الاختصار | المشرف: {interaction.user}")
                await interaction.followup.send(embed=EmbedBuilder.success("تم فك العزل", f"✅ تم فك التايم أوت (العزل) عن {member.mention} بنجاح."), ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send(embed=EmbedBuilder.error("خطأ الصلاحية", "❌ لا يمتلك البوت صلاحية كافية لفك التايم عن هذا العضو."), ephemeral=True)
            except Exception as e:
                await interaction.followup.send(embed=EmbedBuilder.error("خطأ", f"❌ حدث خطأ: {e}"), ephemeral=True)
        elif self.action == "kick":
            await interaction.response.send_modal(ShortcutKickModal(member))
        elif self.action == "ban":
            await interaction.response.send_modal(ShortcutBanModal(member))
        elif self.action == "delete_warn":
            await interaction.response.send_modal(ShortcutDeleteWarnModal(member))
        elif self.action in ["warnings", "warns"]:
            await interaction.response.defer(ephemeral=True)
            async with AsyncSessionLocal() as session:
                service = WarningService(session)
                warnings_list = await service.get_warnings(interaction.guild.id, member.id)
                if not warnings_list:
                    await interaction.followup.send(embed=EmbedBuilder.info("سجل التحذيرات", f"✅ لا توجد أي تحذيرات مسجلة للعضو {member.mention}."), ephemeral=True)
                    return

                status_badges = {
                    "ACTIVE": "🟢 نشط",
                    "EXPIRED": "⚪ منتهي",
                    "REMOVED": "🔴 محذوف",
                    "VOIDED": "🟡 ملغى"
                }

                embed = discord.Embed(
                    title=f"📋 سجل تحذيرات | {member.display_name}",
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_thumbnail(url=member.display_avatar.url)

                for w in warnings_list[:10]:
                    moderator = interaction.guild.get_member(w.moderator_id)
                    mod_str = moderator.mention if moderator else f"`{w.moderator_id}`"
                    status_str = status_badges.get(w.status, w.status)
                    type_str = "رسمي" if w.warning_type == "formal" else "شفهي"
                    exp_str = f"<t:{int(w.expires_at.timestamp())}:R>" if w.expires_at else "دائم"

                    embed.add_field(
                        name=f"#{w.local_id} | ({type_str}) - {status_str}",
                        value=f"**السبب:** {w.reason}\n**المشرف:** {mod_str}\n**الانتهاء:** {exp_str}\n**التاريخ:** <t:{int(w.created_at.timestamp())}:D>",
                        inline=False
                    )

                embed.set_footer(text=f"إجمالي التحذيرات: {len(warnings_list)}")
                await interaction.followup.send(embed=embed, ephemeral=True)
        elif self.action in ["balance", "bal"]:
            await interaction.response.defer(ephemeral=True)
            async with AsyncSessionLocal() as session:
                eco_svc = EconomyService(session)
                bal, bank_bal, total = await eco_svc.get_balance(member.id)
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
        elif self.action == "profile":
            await interaction.response.defer(ephemeral=True)
            async with AsyncSessionLocal() as session:
                profile_svc = ProfileService(session)
                embed, card_file = await profile_svc.build_profile_card_file(member)
                if card_file:
                    await interaction.followup.send(file=card_file, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
        elif self.action == "voice_mute":
            await interaction.response.defer(ephemeral=True)
            async with AsyncSessionLocal() as session:
                service = VoiceService(session)
                count, errs = await service.set_mute_state(interaction.guild, interaction.user, True, member=member, reason="Shortcut Mute")
                if count > 0:
                    await interaction.followup.send(f"✅ تم كتم صوت {member.mention} بنجاح.", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ فشل: {', '.join(errs)}", ephemeral=True)
        elif self.action == "voice_unmute":
            await interaction.response.defer(ephemeral=True)
            async with AsyncSessionLocal() as session:
                service = VoiceService(session)
                count, errs = await service.set_mute_state(interaction.guild, interaction.user, False, member=member, reason="Shortcut Unmute")
                if count > 0:
                    await interaction.followup.send(f"✅ تم فك كتم صوت {member.mention} بنجاح.", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ فشل: {', '.join(errs)}", ephemeral=True)
        elif self.action == "voice_move":
            if not member.voice or not member.voice.channel:
                await interaction.response.send_message(f"❌ العضو {member.mention} ليس متواجدًا في أي روم صوتي لنقله!", ephemeral=True)
                return
            view = ShortcutMoveVoiceChannelView(target_member=member, author=self.author)
            await interaction.response.send_message(f"اختر الروم الصوتي لنقل {member.mention}:", view=view, ephemeral=True)
        elif self.action == "voice_disconnect":
            await interaction.response.defer(ephemeral=True)
            async with AsyncSessionLocal() as session:
                service = VoiceService(session)
                count, errs = await service.disconnect_members(interaction.guild, interaction.user, member=member, reason="Shortcut Disconnect")
                if count > 0:
                    await interaction.followup.send(f"✅ تم فصل {member.mention} من الروم الصوتي بنجاح.", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ فشل: {', '.join(errs)}", ephemeral=True)

# --- SHORTCUT COG ---

class ShortcutsCog(commands.Cog):
    """Cog for Custom Trigger Words & Shortcuts (e.g. typing 'تحذير' opens warning window)"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    shortcut_group = app_commands.Group(name="shortcut", description="إدارة وتخصيص الكلمات المفتاحية واختصارات الأوامر")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        text = message.content.strip()
        if not text or len(text) > 80:
            return

        words = text.split()
        if not words:
            return

        # Check if the text matches a registered shortcut
        async with AsyncSessionLocal() as session:
            repo = ShortcutRepository(session)
            
            # 1. Try matching exact text, 2-word trigger, or first-word trigger
            shortcut = await repo.get_shortcut(message.guild.id, text)
            if not shortcut and len(words) >= 2:
                shortcut = await repo.get_shortcut(message.guild.id, f"{words[0]} {words[1]}")
            if not shortcut:
                shortcut = await repo.get_shortcut(message.guild.id, words[0])

            if not shortcut:
                # If no shortcuts exist for guild, seed defaults once
                all_sc = await repo.list_shortcuts(message.guild.id)
                if not all_sc:
                    await repo.seed_defaults_if_empty(message.guild.id, message.guild.owner_id or message.author.id)
                    shortcut = await repo.get_shortcut(message.guild.id, text)
                    if not shortcut and len(words) >= 2:
                        shortcut = await repo.get_shortcut(message.guild.id, f"{words[0]} {words[1]}")
                    if not shortcut:
                        shortcut = await repo.get_shortcut(message.guild.id, words[0])

            if not shortcut or not shortcut.enabled:
                return

            # Check Channel Restrictions
            if shortcut.ignored_channels:
                ignored_list = [int(cid.strip()) for cid in shortcut.ignored_channels.split(",") if cid.strip().isdigit()]
                if message.channel.id in ignored_list:
                    return

            if shortcut.allowed_channels:
                allowed_list = [int(cid.strip()) for cid in shortcut.allowed_channels.split(",") if cid.strip().isdigit()]
                if allowed_list and message.channel.id not in allowed_list:
                    return

            # Check User / Role Restrictions
            perm_service = PermissionService(session)
            is_admin = await perm_service.is_server_admin(message.author) or settings.is_bot_owner(message.author.id)

            user_rids = [r.id for r in message.author.roles]

            # Check Ignored / Excluded Roles
            if shortcut.ignored_roles:
                ignored_rids = [int(rid.strip()) for rid in shortcut.ignored_roles.split(",") if rid.strip().isdigit()]
                if any(r in ignored_rids for r in user_rids) and not settings.is_bot_owner(message.author.id):
                    return

            if not is_admin:
                if shortcut.allowed_users:
                    allowed_uids = [int(uid.strip()) for uid in shortcut.allowed_users.split(",") if uid.strip().isdigit()]
                    if allowed_uids and message.author.id not in allowed_uids:
                        return

                if shortcut.allowed_roles:
                    allowed_rids = [int(rid.strip()) for rid in shortcut.allowed_roles.split(",") if rid.strip().isdigit()]
                    if allowed_rids and not any(r in allowed_rids for r in user_rids):
                        return

            # Execute / Prompt the Shortcut Action
            action = shortcut.target_action.lower()

            if action in ["warn", "timeout", "untimeout", "kick", "ban", "delete_warn", "warnings", "warns", "voice_mute", "voice_unmute", "voice_disconnect", "voice_move"]:
                action_names = {
                    "warn": ("⚠️ إصدار تحذير سريع", "اختر العضو لإدخال سبب التحذير ورابط الدليل:"),
                    "timeout": ("⏱️ عزل مؤقت (Timeout)", "اختر العضو لإدخال المدة والسبب ورابط الدليل:"),
                    "untimeout": ("⏱️ فك العزل المؤقت (Untimeout)", "اختر العضو لفك التايم أوت عنه:"),
                    "kick": ("👢 طرد عضو", "اختر العضو لإدخال سبب الطرد ورابط الدليل:"),
                    "ban": ("🔨 حظر عضو", "اختر العضو لإدخال سبب الحظر ورابط الدليل:"),
                    "delete_warn": ("🗑️ حذف تحذير معين", "اختر العضو لإدخال رقم التحذير المراد حذفه:"),
                    "warnings": ("📋 عرض سجل التحذيرات", "اختر العضو لعرض قائمة تحذيراته (أو اختر نفسك):"),
                    "warns": ("📋 عرض سجل التحذيرات", "اختر العضو لعرض قائمة تحذيراته (أو اختر نفسك):"),
                    "voice_mute": ("🔇 كتم صوت", "اختر العضو لكتم صوته:"),
                    "voice_unmute": ("🔊 فك كتم الصوت", "اختر العضو لفك كتم صوته:"),
                    "voice_disconnect": ("🔌 فصل من الصوت", "اختر العضو لفصله من الروم الصوتي:"),
                    "voice_move": ("🎙️ نقل عضو لروم صوتي", "اختر العضو المراد نقله إلى روم صوتي آخر:"),
                }
                title, desc = action_names.get(action, ("⚡ اختصار إداري", "اختر العضو المطلوب:"))
                embed = discord.Embed(
                    title=f"⚡ {title} | نافذة الاختصار",
                    description=f"{desc}\n👤 **بواسطة:** {message.author.mention}",
                    color=discord.Color.gold()
                )
                view = ShortcutActionMemberSelectView(action=action, author=message.author)
                try:
                    await message.reply(embed=embed, view=view, delete_after=120)
                except Exception:
                    await message.channel.send(embed=embed, view=view, delete_after=120)

            elif action == "purge":
                embed = discord.Embed(
                    title="🧹 مسح الرسائل السريع",
                    description="اضغط على الزر أدناه لإدخال عدد الرسائل المراد مسحها:",
                    color=discord.Color.dark_teal()
                )
                class PurgeBtnView(ui.View):
                    def __init__(self, author):
                        super().__init__(timeout=60)
                        self.author = author
                    @ui.button(label="مسح الرسائل", style=discord.ButtonStyle.danger, emoji="🧹")
                    async def purge_click(self, inter: discord.Interaction, btn: ui.Button):
                        if inter.user.id != self.author.id:
                            await inter.response.send_message("❌ مخصص لمن طلب الاختصار فقط!", ephemeral=True)
                            return
                        await inter.response.send_modal(ShortcutPurgeModal())

                await message.reply(embed=embed, view=PurgeBtnView(message.author), delete_after=60)

            elif action in ["lock", "unlock"]:
                if action == "lock":
                    overwrite = message.channel.overwrites_for(message.guild.default_role)
                    overwrite.send_messages = False
                    await message.channel.set_permissions(message.guild.default_role, overwrite=overwrite, reason="Locked via shortcut")
                    await message.channel.send("🔒 تم قفل هذه القناة النصية بنجاح.")
                else:
                    overwrite = message.channel.overwrites_for(message.guild.default_role)
                    overwrite.send_messages = None
                    await message.channel.set_permissions(message.guild.default_role, overwrite=overwrite, reason="Unlocked via shortcut")
                    await message.channel.send("🔓 تم فتح هذه القناة النصية بنجاح.")

            elif action == "profile":
                target_user = message.mentions[0] if message.mentions else message.author
                profile_svc = ProfileService(session)
                embed, card_file = await profile_svc.build_profile_card_file(target_user)
                view = ProfileView(target_user)
                if card_file:
                    await message.reply(file=card_file, view=view)
                else:
                    await message.reply(embed=embed, view=view)

            elif action in ["balance", "bal"]:
                target_user = message.mentions[0] if message.mentions else message.author
                eco_svc = EconomyService(session)
                bal, bank_bal, total = await eco_svc.get_balance(target_user.id)
                embed = discord.Embed(
                    title=f"💰 تفاصيل الرصيد | {target_user.display_name}",
                    description=(
                        f"• 💵 **المحفظة:** `{bal:,}` {settings.CURRENCY_EMOJI}\n"
                        f"• 🏦 **البنك:** `{bank_bal:,}` {settings.CURRENCY_EMOJI}\n"
                        f"• ✨ **الإجمالي:** **`{total:,}` {settings.CURRENCY_NAME}**"
                    ),
                    color=discord.Color.gold(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_thumbnail(url=target_user.display_avatar.url)
                await message.reply(embed=embed)

            elif action == "shop":
                shop_svc = ShopService(session)
                products = await shop_svc.list_products(enabled_only=True)
                banners = [p for p in products if p.type in ["BANNER", "COSMETIC"]]
                if banners:
                    carousel = BannerCarouselView(banners, message.author.id, 0)
                    em = await carousel.get_current_embed(message.author.id)
                    await message.reply(embed=em, view=carousel)
                else:
                    await message.reply("🛒 لا توجد بانرات معروضة في المتجر حالياً.")

            elif action == "daily":
                eco_svc = EconomyService(session)
                success, msg, amount, streak = await eco_svc.claim_daily(message.author.id)
                if success:
                    await message.reply(embed=EmbedBuilder.success("المكافأة اليومية", msg))
                else:
                    await message.reply(embed=EmbedBuilder.warning("عذراً", msg))

            elif action in ["warnings", "warns"]:
                warn_svc = WarningService(session)
                warnings_list = await warn_svc.get_warnings(message.guild.id, message.author.id)
                if not warnings_list:
                    await message.reply("✅ سجلك نظيف تماماً! لا توجد عليك أي تحذيرات مسجلة.")
                else:
                    lines = [f"`#{w.local_id}` - **{w.reason}** (نوع: `{w.warning_type}`) <t:{int(w.created_at.timestamp())}:R>" for w in warnings_list[:10]]
                    embed = discord.Embed(
                        title=f"⚠️ سجل تحذيراتك | {message.author.display_name}",
                        description="\n".join(lines),
                        color=discord.Color.orange()
                    )
                    await message.reply(embed=embed)

            elif action in ["top", "leaderboard", "top_text", "top_voice"]:
                from bot.services.activity_service import ActivityService
                from bot.cogs.leaderboard import LeaderboardView

                act_type = "voice" if action == "top_voice" else "text"
                act_svc = ActivityService(session)
                embed, file = await act_svc.build_leaderboard(
                    guild=message.guild,
                    activity_type=act_type,
                    period="daily"
                )
                view = LeaderboardView(
                    guild=message.guild,
                    current_type=act_type,
                    current_period="daily",
                    requester_id=message.author.id
                )
                attachments = [file] if file else []
                await message.reply(embed=embed, files=attachments, view=view)

    # --- ADMIN SLASH COMMANDS FOR MANAGING SHORTCUTS ---

    @shortcut_group.command(name="add", description="إنشاء أو تعديل اختصار نصي للأوامر وتحديد رتب متعددة مسموحة أو مستثناة")
    @app_commands.describe(
        trigger="الكلمة المفتاحية (مثال: تحذير، كتم، طرد، حظر، مسح، قفل، بروفايل)",
        action="الإجراء المنفذ عند كتابة الكلمة",
        allowed_role="رتبة مسموح لها استخدام الاختصار (اختياري)",
        allowed_roles="رتب مسموحة متعددة (منشن أو أيديهات مفصولة بمسافة أو فاصلة)",
        ignored_role="رتبة مستثناة وممنوعة من استخدام الاختصار (اختياري)",
        ignored_roles="رتب مستثناة وممنوعة متعددة (منشن أو أيديهات)",
        allowed_channel="قناة مسموح بالاختصار فيها فقط (اختياري)",
        ignored_channel="قناة ممنوع فيها الاختصار (اختياري)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="تحذير (Warn + Proof Modal)", value="warn"),
        app_commands.Choice(name="عزل / كتم شات (Timeout + Proof Modal)", value="timeout"),
        app_commands.Choice(name="فك العزل / فك تايم أوت (Untimeout)", value="untimeout"),
        app_commands.Choice(name="طرد (Kick + Proof Modal)", value="kick"),
        app_commands.Choice(name="حظر (Ban + Proof Modal)", value="ban"),
        app_commands.Choice(name="مسح رسائل (Purge Modal)", value="purge"),
        app_commands.Choice(name="قفل القناة (Lock Channel)", value="lock"),
        app_commands.Choice(name="فتح القناة (Unlock Channel)", value="unlock"),
        app_commands.Choice(name="حذف تحذير معين (Delete Specific Warn)", value="delete_warn"),
        app_commands.Choice(name="كتم صوت (Voice Mute)", value="voice_mute"),
        app_commands.Choice(name="فك كتم صوت (Voice Unmute)", value="voice_unmute"),
        app_commands.Choice(name="فصل من الصوت (Voice Disconnect)", value="voice_disconnect"),
        app_commands.Choice(name="نقل عضو لروم صوتي (Voice Move)", value="voice_move"),
        app_commands.Choice(name="عرض البروفايل (Profile)", value="profile"),
        app_commands.Choice(name="عرض الرصيد (Balance)", value="balance"),
        app_commands.Choice(name="فتح متجر البانرات (Banner Shop)", value="shop"),
        app_commands.Choice(name="المكافأة اليومية (Daily)", value="daily"),
        app_commands.Choice(name="سجل التحذيرات (Warnings)", value="warnings"),
        app_commands.Choice(name="لوحة المتصدرين (Leaderboard / Top)", value="top"),
        app_commands.Choice(name="توب الكتابة (Text Top)", value="top_text"),
        app_commands.Choice(name="توب الفويس (Voice Top)", value="top_voice"),
    ])
    async def shortcut_add(
        self,
        interaction: discord.Interaction,
        trigger: str,
        action: app_commands.Choice[str],
        allowed_role: Optional[discord.Role] = None,
        allowed_roles: Optional[str] = None,
        ignored_role: Optional[discord.Role] = None,
        ignored_roles: Optional[str] = None,
        allowed_channel: Optional[discord.TextChannel] = None,
        ignored_channel: Optional[discord.TextChannel] = None
    ):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.is_server_admin(interaction.user):
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "هذا الأمر مخصص فقط لإدارة السيرفر!"), ephemeral=True)
                return

            import re
            # Extract allowed role IDs
            allowed_ids_set = set()
            if allowed_role:
                allowed_ids_set.add(allowed_role.id)
            if allowed_roles:
                for match in re.findall(r"\d+", allowed_roles):
                    allowed_ids_set.add(int(match))

            # Extract ignored role IDs
            ignored_ids_set = set()
            if ignored_role:
                ignored_ids_set.add(ignored_role.id)
            if ignored_roles:
                for match in re.findall(r"\d+", ignored_roles):
                    ignored_ids_set.add(int(match))

            allowed_roles_str = ",".join(str(i) for i in allowed_ids_set) if allowed_ids_set else None
            ignored_roles_str = ",".join(str(i) for i in ignored_ids_set) if ignored_ids_set else None

            repo = ShortcutRepository(session)
            sc = await repo.add_or_update_shortcut(
                guild_id=interaction.guild.id,
                trigger_word=trigger,
                target_action=action.value,
                created_by=interaction.user.id,
                allowed_roles=allowed_roles_str,
                ignored_roles=ignored_roles_str,
                allowed_channels=str(allowed_channel.id) if allowed_channel else None,
                ignored_channels=str(ignored_channel.id) if ignored_channel else None,
                enabled=True
            )

            allowed_mentions = " ".join(f"<@&{r}>" for r in allowed_ids_set) if allowed_ids_set else "الجميع حسب الصلاحية"
            ignored_mentions = " ".join(f"<@&{r}>" for r in ignored_ids_set) if ignored_ids_set else "لا يوجد"

            msg = (
                f"✅ تم بنجاح حفظ الاختصار **`{trigger}`**:\n"
                f"• **الإجراء:** `{action.name}`\n"
                f"• **الرتب المسموحة:** {allowed_mentions}\n"
                f"• **الرتب المستثناة (المحظورة):** {ignored_mentions}\n"
                f"• **القناة المسموحة:** {allowed_channel.mention if allowed_channel else 'كافة القنوات'}\n"
                f"• **القناة المحظورة:** {ignored_channel.mention if ignored_channel else 'لا يوجد'}"
            )
            await interaction.followup.send(embed=EmbedBuilder.success("تم حفظ وتخصيص الاختصار", msg), ephemeral=True)

    @shortcut_group.command(name="remove", description="حذف اختصار مسجل")
    @app_commands.describe(trigger="الكلمة المفتاحية المراد حذفها")
    async def shortcut_remove(self, interaction: discord.Interaction, trigger: str):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.is_server_admin(interaction.user):
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "هذا الأمر مخصص فقط لإدارة السيرفر!"), ephemeral=True)
                return

            repo = ShortcutRepository(session)
            deleted = await repo.delete_shortcut(interaction.guild.id, trigger)
            if deleted:
                await interaction.followup.send(embed=EmbedBuilder.success("تم الحذف", f"تم حذف الاختصار **`{trigger}`** بنجاح."), ephemeral=True)
            else:
                await interaction.followup.send(embed=EmbedBuilder.error("غير موجود", f"لم يتم العثور على اختصار باسم **`{trigger}`**!"), ephemeral=True)

    @shortcut_group.command(name="list", description="عرض كافة الاختصارات والكلمات المفتاحية النشطة في السيرفر")
    async def shortcut_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            repo = ShortcutRepository(session)
            shortcuts = await repo.list_shortcuts(interaction.guild.id)
            if not shortcuts:
                # Seed defaults and re-fetch
                await repo.seed_defaults_if_empty(interaction.guild.id, interaction.user.id)
                shortcuts = await repo.list_shortcuts(interaction.guild.id)

            lines = []
            for sc in shortcuts:
                st = "✅" if sc.enabled else "❌"
                role_info = f" | رتبة: <@&{sc.allowed_roles}>" if sc.allowed_roles else ""
                lines.append(f"{st} **`{sc.trigger_word}`** ➔ `{sc.target_action}`{role_info}")

            embed = EmbedBuilder.info(
                title=f"⚡ اختصارات الأوامر النصية المخصصة ({len(shortcuts)})",
                description="عند كتابة أي من الكلمات أدناه في الشات، يقوم البوت فوراً بفتح النافذة المناسبة لتنفيذ الإجراء مع طلب الدليل:\n\n" + "\n".join(lines[:30])
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ShortcutsCog(bot))
