import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.audit_logs import get_audit_log_executor, format_mention, format_id
from bot.utils.embeds import EmbedBuilder
from bot.utils.time import utc_now

PERMISSIONS_ARABIC = {
    "administrator": "مسؤول كامل (Administrator)",
    "view_audit_log": "عرض سجل الأحداث (View Audit Log)",
    "manage_guild": "إدارة السيرفر (Manage Server)",
    "manage_roles": "إدارة الرتب (Manage Roles)",
    "manage_channels": "إدارة القنوات (Manage Channels)",
    "kick_members": "طرد الأعضاء (Kick Members)",
    "ban_members": "حظر الأعضاء (Ban Members)",
    "create_instant_invite": "إنشاء رابط دعوة",
    "change_nickname": "تغيير الاسم المستعار",
    "manage_nicknames": "إدارة الأسماء المستعارة",
    "manage_emojis": "إدارة الإيموجي",
    "manage_emojis_and_stickers": "إدارة الإيموجي والملصقات",
    "manage_webhooks": "إدارة الويبهوك (Webhooks)",
    "view_channel": "رؤية القنوات (View Channels)",
    "send_messages": "إرسال رسائل (Send Messages)",
    "send_tts_messages": "إرسال رسائل صوتية TTS",
    "manage_messages": "إدارة الرسائل (Manage Messages)",
    "embed_links": "تضمين الروابط (Embed Links)",
    "attach_files": "إرفاق الملفات (Attach Files)",
    "read_message_history": "قراءة سجل الرسائل",
    "mention_everyone": "منشن الجميع (@everyone / @here)",
    "use_external_emojis": "استخدام إيموجي خارجي",
    "view_guild_insights": "عرض إحصائيات السيرفر",
    "connect": "الاتصال بالصوت (Connect)",
    "speak": "التحدث بالصوت (Speak)",
    "mute_members": "كتم صوت الأعضاء (Mute Members)",
    "deafen_members": "صم آذان الأعضاء (Deafen Members)",
    "move_members": "نقل الأعضاء (Move Members)",
    "use_voice_activation": "استخدام تحسس الصوت",
    "priority_speaker": "متحدث ذو أولوية",
    "stream": "بث فيديو/شاشة (Stream)",
    "request_to_speak": "طلب التحدث (Stage)",
    "manage_events": "إدارة الفعاليات (Manage Events)",
    "manage_threads": "إدارة المواضيع (Manage Threads)",
    "create_public_threads": "إنشاء مواضيع عامة",
    "create_private_threads": "إنشاء مواضيع خاصة",
    "external_stickers": "استخدام ملصقات خارجية",
    "send_messages_in_threads": "إرسال رسائل بالمواضيع",
    "use_embedded_activities": "استخدام الأنشطة والألعاب",
    "moderate_members": "عزل/إسكات الأعضاء (Timeout)"
}

def register_role_logs_events(bot: commands.Bot):
    @bot.event
    async def on_guild_role_create(role: discord.Role):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            fields = [
                ("🛡️ الرتبة", role.mention, True),
                ("🏷️ الاسم", f"`{role.name}`", True),
                ("🆔 المعرف", format_id(role.id), True),
                ("🎨 اللون", f"`{role.color}`", True),
                ("📊 الترتيب", f"`{role.position}`", True)
            ]
            
            executor = await get_audit_log_executor(role.guild, discord.AuditLogAction.role_create, role.id)
            if executor:
                fields.append(("👮 أنشئت بواسطة", executor.mention, False))

            embed = EmbedBuilder.log(
                title="🛡️ تم إنشاء رتبة جديدة",
                color=discord.Color.green(),
                fields=fields
            )
            await log_service.log_event(role.guild, "role", embed)

    @bot.event
    async def on_guild_role_delete(role: discord.Role):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            fields = [
                ("🛡️ الرتبة", f"`{role.name}`", True),
                ("🆔 المعرف", format_id(role.id), True),
                ("🎨 اللون", f"`{role.color}`", True),
                ("📊 الترتيب", f"`{role.position}`", True)
            ]
            
            executor = await get_audit_log_executor(role.guild, discord.AuditLogAction.role_delete, role.id)
            if executor:
                fields.append(("👮 حذفت بواسطة", executor.mention, False))

            embed = EmbedBuilder.log(
                title="🗑️ تم حذف رتبة",
                color=discord.Color.red(),
                fields=fields
            )
            await log_service.log_event(role.guild, "role", embed)

    @bot.event
    async def on_guild_role_update(before: discord.Role, after: discord.Role):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            changes = []
            if before.name != after.name:
                changes.append(f"🔹 **الاسم:** `{before.name}` ➔ `{after.name}`")
            if before.color != after.color:
                changes.append(f"🔹 **اللون:** `{before.color}` ➔ `{after.color}`")
            if before.hoist != after.hoist:
                val = "نعم (مفصول)" if after.hoist else "لا (غير مفصول)"
                changes.append(f"🔹 **عرض الأعضاء بشكل منفصل:** `{val}`")
            if before.mentionable != after.mentionable:
                val = "نعم (متاح للجميع)" if after.mentionable else "لا (غير متاح)"
                changes.append(f"🔹 **قابلة للمنشن:** `{val}`")
            if before.position != after.position:
                changes.append(f"🔹 **ترتيب الرتبة:** `{before.position}` ➔ `{after.position}`")
            if getattr(before, "icon", None) != getattr(after, "icon", None):
                changes.append("🔹 **تغيير أيقونة الرتبة (Icon)**")
            if getattr(before, "unicode_emoji", None) != getattr(after, "unicode_emoji", None):
                changes.append(f"🔹 **الإيموجي:** `{before.unicode_emoji}` ➔ `{after.unicode_emoji}`")

            # Detailed Permissions Comparison
            if before.permissions != after.permissions:
                granted_perms = []
                revoked_perms = []
                for perm, val in iter(after.permissions):
                    before_val = getattr(before.permissions, perm, False)
                    if val and not before_val:
                        perm_name = PERMISSIONS_ARABIC.get(perm, perm.replace("_", " ").title())
                        granted_perms.append(perm_name)
                    elif not val and before_val:
                        perm_name = PERMISSIONS_ARABIC.get(perm, perm.replace("_", " ").title())
                        revoked_perms.append(perm_name)

                if granted_perms:
                    formatted_granted = "\n".join([f"  ➕ `{p}`" for p in granted_perms])
                    changes.append(f"✅ **صلاحيات تم تفعيلها/منحها:**\n{formatted_granted}")

                if revoked_perms:
                    formatted_revoked = "\n".join([f"  ➖ `{p}`" for p in revoked_perms])
                    changes.append(f"❌ **صلاحيات تم تعطيلها/سحبها:**\n{formatted_revoked}")
                
            if not changes:
                return

            fields = [
                ("🛡️ الرتبة", after.mention, True),
                ("🆔 المعرف", format_id(after.id), True),
                ("📝 تفاصيل التعديلات", "\n\n".join(changes), False)
            ]
            
            executor = await get_audit_log_executor(after.guild, discord.AuditLogAction.role_update, after.id)
            if executor:
                fields.append(("👮 عدلت بواسطة", executor.mention, False))

            embed = EmbedBuilder.log(
                title="🛡️ تم تعديل رتبة بتفصيل كامل",
                color=discord.Color.gold(),
                fields=fields
            )
            await log_service.log_event(after.guild, "role", embed)


