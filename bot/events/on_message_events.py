import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.embeds import EmbedBuilder
from bot.utils.logger import logger
from bot.utils.time import utc_now

def register_message_logs_events(bot: commands.Bot):
    
    @bot.event
    async def on_message_delete(message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            # Create Embed
            embed = discord.Embed(
                title="🗑️ Message Deleted",
                color=discord.Color.red(),
                timestamp=utc_now()
            )
            embed.set_author(name=f"{message.author} ({message.author.id})", icon_url=message.author.display_avatar.url if message.author.display_avatar else None)
            embed.add_field(name="Channel", value=f"{message.channel.mention} (`{message.channel.id}`)", inline=False)
            
            if message.content:
                # Truncate content if too long
                content = message.content[:1020] + "..." if len(message.content) > 1024 else message.content
                embed.add_field(name="Content", value=content, inline=False)
                
            if message.attachments:
                attachments = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
                embed.add_field(name="Attachments", value=attachments[:1024], inline=False)
                
            embed.set_footer(text=f"Message ID: {message.id}")
            
            # Fetch audit logs to see if someone else deleted it
            try:
                # Small delay to ensure audit log is created
                import asyncio
                await asyncio.sleep(1)
                async for entry in message.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1):
                    if entry.target.id == message.author.id and entry.extra.channel.id == message.channel.id:
                        # Ensure it's recent
                        if (utc_now() - entry.created_at).total_seconds() < 10:
                            embed.add_field(name="Deleted By", value=f"{entry.user.mention} (`{entry.user.id}`)", inline=False)
                        break
            except Exception as e:
                logger.error(f"Error fetching audit logs for message delete: {e}")
                
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
            
            embed = discord.Embed(
                title="🗑️ Bulk Message Delete",
                color=discord.Color.red(),
                timestamp=utc_now()
            )
            if channel:
                embed.add_field(name="Channel", value=f"{channel.mention} (`{channel.id}`)", inline=False)
            embed.add_field(name="Count", value=f"`{len(payload.message_ids)}` messages deleted.", inline=False)
            
            # Try to fetch audit logs for bulk delete
            try:
                import asyncio
                await asyncio.sleep(1)
                async for entry in guild.audit_logs(action=discord.AuditLogAction.message_bulk_delete, limit=1):
                    if entry.extra.count == len(payload.message_ids) and entry.target.id == payload.channel_id:
                        if (utc_now() - entry.created_at).total_seconds() < 10:
                            embed.add_field(name="Deleted By", value=f"{entry.user.mention} (`{entry.user.id}`)", inline=False)
                        break
            except Exception:
                pass
                
            await log_service.log_event(guild, "message", embed)

    @bot.event
    async def on_message_edit(before: discord.Message, after: discord.Message):
        if before.author.bot or before.guild is None:
            return
        if before.content == after.content: # Could be pin/unpin or embed generation
            return
            
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            embed = discord.Embed(
                title="✏️ Message Edited",
                color=discord.Color.gold(),
                timestamp=utc_now()
            )
            embed.set_author(name=f"{before.author} ({before.author.id})", icon_url=before.author.display_avatar.url if before.author.display_avatar else None)
            embed.add_field(name="Channel", value=f"{before.channel.mention} (`{before.channel.id}`)", inline=False)
            
            b_content = before.content[:1020] + "..." if len(before.content) > 1024 else (before.content or "None")
            a_content = after.content[:1020] + "..." if len(after.content) > 1024 else (after.content or "None")
            
            embed.add_field(name="Before", value=b_content, inline=False)
            embed.add_field(name="After", value=a_content, inline=False)
            embed.add_field(name="Message Link", value=f"[Jump to Message]({after.jump_url})", inline=False)
            embed.set_footer(text=f"Message ID: {after.id}")
            
            await log_service.log_event(before.guild, "message", embed)

