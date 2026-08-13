import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.audit_logs import get_audit_log_executor, format_mention, format_id
from bot.utils.embeds import EmbedBuilder

def register_voice_logs_events(bot: commands.Bot):
    @bot.event
    async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.guild is None or member.bot:
            return
            
        # Avoid logging if no significant change happened (e.g. just deafened but not moved)
        # We only care about Join, Leave, Move, and Admin Actions for now based on user request
        
        async with AsyncSessionLocal() as session:
            try:
                log_service = LogService(session)
                
                # Voice Join
                if before.channel is None and after.channel is not None:
                    fields = [
                        ("👤 العضو", member.mention, True),
                        ("🆔 المعرف", format_id(member.id), True),
                        ("🔊 القناة", after.channel.mention, True)
                    ]
                    embed = EmbedBuilder.log(
                        title="🎙️ دخول روم صوتي",
                        color=discord.Color.green(),
                        fields=fields,
                        author=member
                    )
                    await log_service.log_event(member.guild, "voice", embed)
                    
                # Voice Leave
                elif before.channel is not None and after.channel is None:
                    fields = [
                        ("👤 العضو", member.mention, True),
                        ("🆔 المعرف", format_id(member.id), True),
                        ("🔇 القناة السابقة", before.channel.mention, True)
                    ]
                    embed = EmbedBuilder.log(
                        title="🔴 خروج من روم صوتي",
                        color=discord.Color.red(),
                        fields=fields,
                        author=member
                    )
                    await log_service.log_event(member.guild, "voice", embed)
                    
                # Voice Move
                elif before.channel is not None and after.channel is not None and before.channel != after.channel:
                    fields = [
                        ("👤 العضو", member.mention, True),
                        ("🆔 المعرف", format_id(member.id), True),
                        ("📤 من", before.channel.mention, True),
                        ("📥 إلى", after.channel.mention, True)
                    ]
                    embed = EmbedBuilder.log(
                        title="🔀 انتقال بين الغرف الصوتية",
                        color=discord.Color.blue(),
                        fields=fields,
                        author=member
                    )
                    await log_service.log_event(member.guild, "voice", embed)
                    
                # Mute/Unmute (Server)
                if before.mute != after.mute:
                    title = "🔇 كتم صوت إداري (Server Mute)" if after.mute else "🔊 إلغاء كتم الصوت الإداري (Server Unmute)"
                    fields = [
                        ("👤 العضو", member.mention, True),
                        ("🆔 المعرف", format_id(member.id), True)
                    ]
                    if after.channel:
                        fields.append(("🔊 القناة", after.channel.mention, True))
                    
                    # Fetch executor for server mute/unmute
                    executor = await get_audit_log_executor(member.guild, discord.AuditLogAction.member_update, member.id)
                    if executor:
                        fields.append(("👮 المنفذ", executor.mention, False))

                    embed = EmbedBuilder.log(
                        title=title,
                        color=discord.Color.orange(),
                        fields=fields,
                        author=member
                    )
                    await log_service.log_event(member.guild, "voice", embed)
                    
                # Deafen/Undeafen (Server)
                if before.deaf != after.deaf:
                    title = "🔕 كتم سماعة إداري (Server Deafen)" if after.deaf else "🔔 إلغاء كتم السماعة الإداري (Server Undeafen)"
                    fields = [
                        ("👤 العضو", member.mention, True),
                        ("🆔 المعرف", format_id(member.id), True)
                    ]
                    if after.channel:
                        fields.append(("🔊 القناة", after.channel.mention, True))
                    
                    executor = await get_audit_log_executor(member.guild, discord.AuditLogAction.member_update, member.id)
                    if executor:
                        fields.append(("👮 المنفذ", executor.mention, False))

                    embed = EmbedBuilder.log(
                        title=title,
                        color=discord.Color.orange(),
                        fields=fields,
                        author=member
                    )
                    await log_service.log_event(member.guild, "voice", embed)

                # Camera start/stop
                if before.self_video != after.self_video:
                    title = "📹 تشغيل الكاميرا" if after.self_video else "📽️ إغلاق الكاميرا"
                    fields = [
                        ("👤 العضو", member.mention, True),
                        ("🔊 القناة", format_mention(after.channel), True)
                    ]
                    embed = EmbedBuilder.log(
                        title=title,
                        color=discord.Color.purple(),
                        fields=fields,
                        author=member
                    )
                    await log_service.log_event(member.guild, "voice", embed)
                    
                # Stream start/stop
                if before.self_stream != after.self_stream:
                    title = "📡 بدء بث مباشر (Streaming)" if after.self_stream else "🛑 إنهاء البث المباشر"
                    fields = [
                        ("👤 العضو", member.mention, True),
                        ("🔊 القناة", format_mention(after.channel), True)
                    ]
                    embed = EmbedBuilder.log(
                        title=title,
                        color=discord.Color.dark_purple(),
                        fields=fields,
                        author=member
                    )
                    await log_service.log_event(member.guild, "voice", embed)
            except Exception as e:
                from bot.utils.logger import logger
                logger.error(f"Error in on_voice_state_update: {e}")

