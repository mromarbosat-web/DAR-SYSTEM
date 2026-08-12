import discord
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.repositories.security_repository import SecurityRepository
from bot.database.repositories.automod_repository import AutoModRepository
from bot.database.repositories.verification_repository import VerificationRepository
from bot.database.repositories.log_repository import LogRepository
from bot.database.repositories.moderation_repository import ModerationRepository
from bot.utils.embeds import EmbedBuilder

class SetupService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.sec_repo = SecurityRepository(session)
        self.automod_repo = AutoModRepository(session)
        self.verif_repo = VerificationRepository(session)
        self.log_repo = LogRepository(session)
        self.mod_repo = ModerationRepository(session)

    async def get_security_status(self, guild: discord.Guild) -> discord.Embed:
        sec = await self.sec_repo.get_security_settings(guild.id)
        
        raid_status = "🟢 مفعّل (Enabled)" if sec.anti_raid_enabled else "🔴 معطل (Disabled)"
        nuke_status = "🟢 مفعّل (Enabled)" if sec.anti_nuke_enabled else "🔴 معطل (Disabled)"

        fields = [
            ("🛡️ حالة Anti-Raid", f"**الحالة:** {raid_status}\n**حد الدخول:** {sec.anti_raid_join_threshold} اعضاء\n**النافذة الزمنية:** {sec.anti_raid_time_window} ثوانٍ\n**الإجراء:** `{sec.anti_raid_action}`", True),
            ("💣 حالة Anti-Nuke", f"**الحالة:** {nuke_status}\n**حد القنوات:** {sec.anti_nuke_channel_threshold}\n**حد الرتب:** {sec.anti_nuke_role_threshold}\n**النافذة الزمنية:** {sec.anti_nuke_time_window} ثوانٍ\n**الإجراء:** `{sec.anti_nuke_action}`", True)
        ]

        return EmbedBuilder.info(
            title=f"تقرير الإعدادات الأمنية لسيرفر {guild.name}",
            description="حالة أنظمة الحماية والأمان (Anti-Raid & Anti-Nuke)",
            fields=fields
        )

    async def get_automod_status(self, guild: discord.Guild) -> discord.Embed:
        automod = await self.automod_repo.get_automod_settings(guild.id)
        status = "🟢 مفعّل (Enabled)" if automod.enabled else "🔴 معطل (Disabled)"

        bad_words_count = len(automod.bad_words or [])
        whitelisted_words_count = len(automod.whitelisted_words or [])
        ignored_channels_count = len(automod.ignored_channels or [])

        fields = [
            ("⚙️ النظام العام", f"**الحالة:** {status}\n**الإجراء المخالف:** `{automod.action}`", True),
            ("⚡ فلاتر الحماية", f"**Spam:** {'نعم' if automod.anti_spam_enabled else 'لا'}\n**منع Invites:** {'نعم' if automod.block_invites else 'لا'}\n**منع Links:** {'نعم' if automod.block_links else 'لا'}", True),
            ("📝 القوائم والحدود", f"**الكلمات المحظورة:** `{bad_words_count}`\n**الكلمات المستثناة:** `{whitelisted_words_count}`\n**القنوات المستثناة:** `{ignored_channels_count}`", True)
        ]

        return EmbedBuilder.info(
            title=f"تقرير إعدادات AutoMod لسيرفر {guild.name}",
            description="تفاصيل فلاتر الإشراف التلقائي وحظر المحتوى المشبوه",
            fields=fields
        )

    async def get_logs_status(self, guild: discord.Guild) -> discord.Embed:
        logs = await self.log_repo.get_log_settings(guild.id)

        def fmt_ch(ch_id):
            if not ch_id:
                return "`غير محدد`"
            ch = guild.get_channel(ch_id)
            return ch.mention if ch else f"`#{ch_id}` (ملاحظة: تعذر العثور عليها)"

        fields = [
            ("👤 Member Logs", fmt_ch(logs.member_log_channel_id), True),
            ("💬 Message Logs", fmt_ch(logs.message_log_channel_id), True),
            ("🔨 Moderation Logs", fmt_ch(logs.moderation_log_channel_id), True),
            ("🎭 Role Logs", fmt_ch(logs.role_log_channel_id), True),
            ("📺 Channel Logs", fmt_ch(logs.channel_log_channel_id), True),
            ("🛡️ Security Logs", fmt_ch(logs.security_log_channel_id), True),
            ("⚙️ Server Logs", fmt_ch(logs.server_log_channel_id), True)
        ]

        return EmbedBuilder.info(
            title=f"قنوات السجلات واللوجز لسيرفر {guild.name}",
            description="قنوات إرسال الأحداث وتوثيق الأنشطة الإدارية والأمنية",
            fields=fields
        )
