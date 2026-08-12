import logging
import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.time import utc_now

logger = logging.getLogger("discord_bot.events.member_remove")

def register_member_remove_event(bot: commands.Bot):
    @bot.event
    async def on_member_remove(member: discord.Member):
        guild = member.guild
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            joined_at = member.joined_at
            stay_duration = f"<t:{int(joined_at.timestamp())}:R>" if joined_at else "Unknown"
            
            embed = discord.Embed(title="👤 Member Left", color=discord.Color.red(), timestamp=utc_now())
            embed.set_author(name=f"{member} ({member.id})", icon_url=member.display_avatar.url if member.display_avatar else None)
            embed.add_field(name="Joined", value=stay_duration, inline=True)
            embed.add_field(name="Member Count", value=f"`{guild.member_count}`", inline=True)
            
            # Check Audit Logs for Kick/Ban
            try:
                import asyncio
                await asyncio.sleep(1)
                
                # Check for kicks
                kicked = False
                async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
                    if entry.target.id == member.id:
                        if (utc_now() - entry.created_at).total_seconds() < 10:
                            embed.add_field(name="Kicked By", value=f"{entry.user.mention} (`{entry.user.id}`)", inline=False)
                            if entry.reason:
                                embed.add_field(name="Reason", value=f"`{entry.reason}`", inline=False)
                            kicked = True
                            break
                            
                # Check for bans (on_member_remove triggers before on_member_ban sometimes, but audit logs might have it)
                if not kicked:
                    async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
                        if entry.target.id == member.id:
                            if (utc_now() - entry.created_at).total_seconds() < 10:
                                embed.add_field(name="Banned By", value=f"{entry.user.mention} (`{entry.user.id}`)", inline=False)
                                if entry.reason:
                                    embed.add_field(name="Reason", value=f"`{entry.reason}`", inline=False)
                                break
            except Exception:
                pass

            await log_service.log_event(guild, "member", embed)
