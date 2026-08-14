import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.audit_logs import get_audit_log_executor, format_mention, format_id
from bot.utils.embeds import EmbedBuilder
from bot.utils.time import utc_now
from bot.events.on_role_events import PERMISSIONS_ARABIC

def register_channel_logs_events(bot: commands.Bot):
    @bot.event
    async def on_guild_channel_create(channel: discord.abc.GuildChannel):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            ch_type_map = {
                discord.ChannelType.text: "نصية (Text)",
                discord.ChannelType.voice: "صوتية (Voice)",
                discord.ChannelType.category: "قسم (Category)",
                discord.ChannelType.news: "أخبار (News)",
                discord.ChannelType.stage_voice: "مسرح (Stage)"
            }
            ch_type = ch_type_map.get(channel.type, str(channel.type))
            
            fields = [
                ("📁 القناة", channel.mention, True),
                ("🏷️ الاسم", f"`{channel.name}`", True),
                ("🆔 المعرف", format_id(channel.id), True),
                ("🛠️ النوع", f"`{ch_type}`", True)
            ]
            
            if hasattr(channel, "category") and channel.category:
                fields.append(("📂 القسم", f"`{channel.category.name}`", True))
                
            executor = await get_audit_log_executor(channel.guild, discord.AuditLogAction.channel_create, channel.id)
            if executor:
                fields.append(("👮 أنشئت بواسطة", executor.mention, False))

            embed = EmbedBuilder.log(
                title="📁 تم إنشاء قناة جديدة",
                color=discord.Color.green(),
                fields=fields
            )
            await log_service.log_event(channel.guild, "channel", embed)

    @bot.event
    async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            ch_type_map = {
                discord.ChannelType.text: "نصية (Text)",
                discord.ChannelType.voice: "صوتية (Voice)",
                discord.ChannelType.category: "قسم (Category)",
                discord.ChannelType.news: "أخبار (News)",
                discord.ChannelType.stage_voice: "مسرح (Stage)"
            }
            ch_type = ch_type_map.get(channel.type, str(channel.type))
            
            fields = [
                ("📁 القناة", f"`{channel.name}`", True),
                ("🆔 المعرف", format_id(channel.id), True),
                ("🛠️ النوع", f"`{ch_type}`", True)
            ]
            
            executor = await get_audit_log_executor(channel.guild, discord.AuditLogAction.channel_delete, channel.id)
            if executor:
                fields.append(("👮 حذفت بواسطة", executor.mention, False))

            embed = EmbedBuilder.log(
                title="🗑️ تم حذف قناة",
                color=discord.Color.red(),
                fields=fields
            )
            await log_service.log_event(channel.guild, "channel", embed)

    @bot.event
    async def on_guild_channel_update(before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            changes = []
            if before.name != after.name:
                changes.append(f"🔹 **الاسم:** `{before.name}` ➔ `{after.name}`")
            
            if hasattr(before, "topic") and hasattr(after, "topic") and before.topic != after.topic:
                b_topic = str(before.topic)[:50] + "..." if before.topic and len(before.topic) > 50 else (before.topic or "بدون موضوع")
                a_topic = str(after.topic)[:50] + "..." if after.topic and len(after.topic) > 50 else (after.topic or "بدون موضوع")
                changes.append(f"🔹 **الموضوع (Topic):** `{b_topic}` ➔ `{a_topic}`")
                
            if hasattr(before, "slowmode_delay") and hasattr(after, "slowmode_delay") and before.slowmode_delay != after.slowmode_delay:
                changes.append(f"🔹 **الوضع الهادئ (Slowmode):** `{before.slowmode_delay}s` ➔ `{after.slowmode_delay}s`")
                
            if hasattr(before, "nsfw") and hasattr(after, "nsfw") and before.nsfw != after.nsfw:
                val = "مفعل (NSFW On)" if after.nsfw else "معطل (NSFW Off)"
                changes.append(f"🔹 **محتوى للبالغين (NSFW):** `{val}`")
                
            if getattr(before, "category_id", None) != getattr(after, "category_id", None):
                b_cat = before.category.name if getattr(before, "category", None) else "بدون قسم"
                a_cat = after.category.name if getattr(after, "category", None) else "بدون قسم"
                changes.append(f"🔹 **القسم (Category):** `{b_cat}` ➔ `{a_cat}`")

            # Voice Channel specific properties
            if hasattr(before, "bitrate") and hasattr(after, "bitrate") and before.bitrate != after.bitrate:
                changes.append(f"🔹 **جودة الصوت (Bitrate):** `{before.bitrate // 1000}kbps` ➔ `{after.bitrate // 1000}kbps`")

            if hasattr(before, "user_limit") and hasattr(after, "user_limit") and before.user_limit != after.user_limit:
                b_limit = f"{before.user_limit} أعضاء" if before.user_limit > 0 else "غير محدود"
                a_limit = f"{after.user_limit} أعضاء" if after.user_limit > 0 else "غير محدود"
                changes.append(f"🔹 **الحد الأقصى للأعضاء (User Limit):** `{b_limit}` ➔ `{a_limit}`")

            # Detailed Overwrites (Permissions) comparison
            if hasattr(before, "overwrites") and hasattr(after, "overwrites") and before.overwrites != after.overwrites:
                b_ow = before.overwrites
                a_ow = after.overwrites
                all_targets = set(b_ow.keys()).union(set(a_ow.keys()))

                for target in all_targets:
                    t_name = target.mention if hasattr(target, "mention") else target.name
                    if target not in b_ow:
                        changes.append(f"🔹 **إضافة صلاحيات خاصة لـ {t_name}**")
                    elif target not in a_ow:
                        changes.append(f"🔹 **إزالة تخصيص الصلاحيات لـ {t_name}**")
                    else:
                        b_perm = b_ow[target]
                        a_perm = a_ow[target]
                        if b_perm != a_perm:
                            perm_diffs = []
                            for perm, val in iter(a_perm):
                                b_val = getattr(b_perm, perm, None)
                                if val != b_val:
                                    p_ar = PERMISSIONS_ARABIC.get(perm, perm.replace("_", " ").title())
                                    if val is True:
                                        perm_diffs.append(f"  ➕ سماح: `{p_ar}`")
                                    elif val is False:
                                        perm_diffs.append(f"  ❌ منع: `{p_ar}`")
                                    else:
                                        perm_diffs.append(f"  ⚪ محايد (افتراضي): `{p_ar}`")
                            if perm_diffs:
                                changes.append(f"🔹 **تعديل صلاحيات {t_name}:**\n" + "\n".join(perm_diffs[:8]))
                
            if not changes:
                return 

            fields = [
                ("📁 القناة", after.mention, True),
                ("🆔 المعرف", format_id(after.id), True),
                ("📝 تفاصيل التعديلات", "\n\n".join(changes), False)
            ]
            
            executor = await get_audit_log_executor(after.guild, discord.AuditLogAction.channel_update, after.id)
            if executor:
                fields.append(("👮 عدلت بواسطة", executor.mention, False))

            embed = EmbedBuilder.log(
                title="📁 تم تعديل قناة بتفصيل كامل",
                color=discord.Color.gold(),
                fields=fields
            )
            await log_service.log_event(after.guild, "channel", embed)


