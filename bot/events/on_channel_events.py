import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.audit_logs import get_audit_log_executor, format_mention, format_id
from bot.utils.embeds import EmbedBuilder
from bot.utils.time import utc_now

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
                changes.append(f"🔹 **الموضوع:** `{b_topic}` ➔ `{a_topic}`")
                
            if hasattr(before, "slowmode_delay") and hasattr(after, "slowmode_delay") and before.slowmode_delay != after.slowmode_delay:
                changes.append(f"🔹 **الوضع الهادئ:** `{before.slowmode_delay}s` ➔ `{after.slowmode_delay}s`")
                
            if hasattr(before, "nsfw") and hasattr(after, "nsfw") and before.nsfw != after.nsfw:
                val = "مفعل" if after.nsfw else "معطل"
                changes.append(f"🔹 **محتوى للبالغين (NSFW):** `{val}`")
                
            if getattr(before, "category_id", None) != getattr(after, "category_id", None):
                b_cat = before.category.name if getattr(before, "category", None) else "بدون قسم"
                a_cat = after.category.name if getattr(after, "category", None) else "بدون قسم"
                changes.append(f"🔹 **القسم:** `{b_cat}` ➔ `{a_cat}`")
                
            if not changes:
                return 

            fields = [
                ("📁 القناة", after.mention, True),
                ("🆔 المعرف", format_id(after.id), True),
                ("📝 التغييرات", "\n".join(changes), False)
            ]
            
            executor = await get_audit_log_executor(after.guild, discord.AuditLogAction.channel_update, after.id)
            if executor:
                fields.append(("👮 عدلت بواسطة", executor.mention, False))

            embed = EmbedBuilder.log(
                title="📁 تم تعديل قناة",
                color=discord.Color.gold(),
                fields=fields
            )
            await log_service.log_event(after.guild, "channel", embed)

