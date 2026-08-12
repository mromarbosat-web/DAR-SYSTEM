import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.embeds import EmbedBuilder
from bot.utils.audit_logs import get_audit_log_executor, format_mention, format_id

def register_message_logs_events(bot: commands.Bot):
    
    @bot.event
    async def on_message_delete(message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            fields = [
                ("👤 صاحب الرسالة", message.author.mention, True),
                ("🆔 معرف المستخدم", format_id(message.author.id), True),
                ("📺 القناة", message.channel.mention, True),
                ("🆔 معرف القناة", format_id(message.channel.id), True)
            ]
            
            if message.content:
                content = message.content[:1020] + "..." if len(message.content) > 1024 else message.content
                fields.append(("📄 محتوى الرسالة", f"```\n{content}\n```", False))
                
            if message.attachments:
                attachments = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
                fields.append(("📎 المرفقات", attachments[:1024], False))
            
            sent_at = f"<t:{int(message.created_at.timestamp())}:F>"
            fields.append(("⏰ وقت الإرسال", sent_at, True))

            # Fetch audit logs to see if someone else deleted it
            executor = await get_audit_log_executor(message.guild, discord.AuditLogAction.message_delete, message.author.id)
            if executor:
                fields.append(("👮 حذف بواسطة", f"{executor.mention} ({executor.id})", False))

            embed = EmbedBuilder.log(
                title="🗑️ تم حذف رسالة",
                color=discord.Color.red(),
                fields=fields,
                author=message.author,
                footer=f"Message ID: {message.id}"
            )
            await log_service.log_event(message.guild, "message", embed)

    @bot.event
    async def on_raw_bulk_message_delete(payload: discord.RawBulkMessageDeleteEvent):
        if payload.guild_id is None:
            return
        
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            return
            
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            channel = guild.get_channel(payload.channel_id)
            
            fields = [
                ("📺 القناة", format_mention(channel), True),
                ("🆔 معرف القناة", format_id(payload.channel_id), True),
                ("🔢 عدد الرسائل", f"`{len(payload.message_ids)}`", True)
            ]
            
            executor = await get_audit_log_executor(guild, discord.AuditLogAction.message_bulk_delete, payload.channel_id)
            if executor:
                fields.append(("👮 المنفذ (Purge)", f"{executor.mention} ({executor.id})", False))

            embed = EmbedBuilder.log(
                title="🧹 حذف رسائل متعددة (Bulk Delete)",
                color=discord.Color.dark_red(),
                fields=fields
            )
            await log_service.log_event(guild, "message", embed)

    @bot.event
    async def on_message_edit(before: discord.Message, after: discord.Message):
        if before.author.bot or before.guild is None:
            return
        if before.content == after.content: 
            return
            
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            b_content = before.content[:1020] + "..." if len(before.content) > 1024 else (before.content or "لا يوجد محتوى نصي")
            a_content = after.content[:1020] + "..." if len(after.content) > 1024 else (after.content or "لا يوجد محتوى نصي")
            
            fields = [
                ("👤 صاحب الرسالة", before.author.mention, True),
                ("📺 القناة", before.channel.mention, True),
                ("🆔 معرف الرسالة", format_id(after.id), True),
                ("📝 المحتوى القديم", f"```\n{b_content}\n```", False),
                ("📝 المحتوى الجديد", f"```\n{a_content}\n```", False),
                ("🔗 رابط الرسالة", f"[انتقال للرسالة]({after.jump_url})", False)
            ]
            
            embed = EmbedBuilder.log(
                title="✏️ تم تعديل رسالة",
                color=discord.Color.gold(),
                fields=fields,
                author=before.author
            )
            await log_service.log_event(before.guild, "message", embed)

