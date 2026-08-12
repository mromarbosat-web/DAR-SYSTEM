import re

with open("bot/events/on_member_events_ext.py", "r") as f:
    content = f.read()

bans = """
    @bot.event
    async def on_member_ban(guild: discord.Guild, user: discord.User):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            embed = discord.Embed(title="🔨 Member Banned", color=discord.Color.red(), timestamp=utc_now())
            embed.set_author(name=f"{user} ({user.id})", icon_url=user.display_avatar.url if user.display_avatar else None)
            
            try:
                import asyncio
                await asyncio.sleep(1)
                async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
                    if entry.target.id == user.id:
                        if (utc_now() - entry.created_at).total_seconds() < 10:
                            embed.add_field(name="Banned By", value=f"{entry.user.mention} (`{entry.user.id}`)", inline=False)
                            if entry.reason:
                                embed.add_field(name="Reason", value=f"`{entry.reason}`", inline=False)
                        break
            except Exception:
                pass
            await log_service.log_event(guild, "moderation", embed)

    @bot.event
    async def on_member_unban(guild: discord.Guild, user: discord.User):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            embed = discord.Embed(title="🔓 Member Unbanned", color=discord.Color.green(), timestamp=utc_now())
            embed.set_author(name=f"{user} ({user.id})", icon_url=user.display_avatar.url if user.display_avatar else None)
            
            try:
                import asyncio
                await asyncio.sleep(1)
                async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, limit=1):
                    if entry.target.id == user.id:
                        if (utc_now() - entry.created_at).total_seconds() < 10:
                            embed.add_field(name="Unbanned By", value=f"{entry.user.mention} (`{entry.user.id}`)", inline=False)
                        break
            except Exception:
                pass
            await log_service.log_event(guild, "moderation", embed)
"""

content += bans

with open("bot/events/on_member_events_ext.py", "w") as f:
    f.write(content)
