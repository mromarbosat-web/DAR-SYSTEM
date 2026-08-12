import logging
import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.audit_logs import get_audit_log_executor, format_mention, format_id
from bot.utils.embeds import EmbedBuilder
from bot.utils.time import utc_now

logger = logging.getLogger("discord_bot.events.member_remove")

def register_member_remove_event(bot: commands.Bot):
    @bot.event
    async def on_member_remove(member: discord.Member):
        guild = member.guild
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            joined_at = member.joined_at
            stay_duration = f"<t:{int(joined_at.timestamp())}:R>" if joined_at else "غير متاح"
            leave_time = f"<t:{int(utc_now().timestamp())}:F>"
            
            fields = [
                ("👤 العضو", member.mention, True),
                ("🆔 معرف المستخدم", format_id(member.id), True),
                ("📥 وقت الانضمام", stay_duration, True),
                ("📤 وقت المغادرة", leave_time, True),
                ("👥 إجمالي الأعضاء", f"`{guild.member_count}`", True)
            ]
            
            # Check Audit Logs for Kick/Ban
            action_type = "🔴 مغادرة عضو"
            mod_fields = []
            
            try:
                # Check for kicks
                async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
                    if entry.target.id == member.id:
                        if (utc_now() - entry.created_at).total_seconds() < 10:
                            action_type = "🚷 طرد عضو (Kick)"
                            fields.append(("👮 المنفذ", entry.user.mention, True))
                            if entry.reason:
                                fields.append(("📝 السبب", f"`{entry.reason}`", False))
                            
                            mod_fields = [
                                ("👤 المستهدف", member.mention, True),
                                ("👮 المنفذ", entry.user.mention, True),
                                ("🛠️ الإجراء", "`KICK`", True),
                                ("📝 السبب", f"`{entry.reason or 'بدون سبب'}`", False)
                            ]
                            break
                            
                # Check for bans
                if action_type == "🔴 مغادرة عضو":
                    async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
                        if entry.target.id == member.id:
                            if (utc_now() - entry.created_at).total_seconds() < 10:
                                action_type = "🚫 حظر عضو (Ban)"
                                fields.append(("👮 المنفذ", entry.user.mention, True))
                                if entry.reason:
                                    fields.append(("📝 السبب", f"`{entry.reason}`", False))
                                
                                mod_fields = [
                                    ("👤 المستهدف", member.mention, True),
                                    ("👮 المنفذ", entry.user.mention, True),
                                    ("🛠️ الإجراء", "`BAN`", True),
                                    ("📝 السبب", f"`{entry.reason or 'بدون سبب'}`", False)
                                ]
                                break
            except Exception:
                pass

            embed = EmbedBuilder.log(
                title=action_type,
                color=discord.Color.red() if action_type == "🔴 مغادرة عضو" else discord.Color.dark_red(),
                fields=fields,
                author=member
            )
            await log_service.log_event(guild, "member", embed)
            
            if mod_fields:
                mod_embed = EmbedBuilder.log(
                    title="🔨 إجراء إداري",
                    color=discord.Color.dark_red(),
                    fields=mod_fields,
                    author=member
                )
                await log_service.log_event(guild, "moderation", mod_embed)
