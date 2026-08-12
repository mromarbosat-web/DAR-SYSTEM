import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.time import utc_now

def register_member_logs_ext_events(bot: commands.Bot):
    @bot.event
    async def on_member_update(before: discord.Member, after: discord.Member):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            # Nickname Change
            if before.nick != after.nick:
                b_nick = before.nick if before.nick else "None"
                a_nick = after.nick if after.nick else "None"
                embed = discord.Embed(title="👤 Nickname Changed", color=discord.Color.blue(), timestamp=utc_now())
                embed.set_author(name=f"{after} ({after.id})", icon_url=after.display_avatar.url if after.display_avatar else None)
                embed.add_field(name="Before", value=f"`{b_nick}`", inline=True)
                embed.add_field(name="After", value=f"`{a_nick}`", inline=True)
                await log_service.log_event(after.guild, "member", embed)
                
            # Role Change
            if before.roles != after.roles:
                added_roles = [r for r in after.roles if r not in before.roles]
                removed_roles = [r for r in before.roles if r not in after.roles]
                
                if added_roles or removed_roles:
                    embed = discord.Embed(title="🛡️ Member Roles Updated", color=discord.Color.gold(), timestamp=utc_now())
                    embed.set_author(name=f"{after} ({after.id})", icon_url=after.display_avatar.url if after.display_avatar else None)
                    if added_roles:
                        embed.add_field(name="Added Roles", value=" ".join([r.mention for r in added_roles]), inline=False)
                    if removed_roles:
                        embed.add_field(name="Removed Roles", value=" ".join([r.mention for r in removed_roles]), inline=False)
                    await log_service.log_event(after.guild, "member", embed)

    @bot.event
    async def on_user_update(before: discord.User, after: discord.User):
        # We need to find mutual guilds to log
        # This can be expensive, maybe just skip or iterate common guilds
        for guild in bot.guilds:
            if guild.get_member(after.id):
                async with AsyncSessionLocal() as session:
                    log_service = LogService(session)
                    if before.name != after.name or before.discriminator != after.discriminator:
                        embed = discord.Embed(title="👤 Username Changed", color=discord.Color.blue(), timestamp=utc_now())
                        embed.set_author(name=f"{after} ({after.id})", icon_url=after.display_avatar.url if after.display_avatar else None)
                        embed.add_field(name="Before", value=f"`{before}`", inline=True)
                        embed.add_field(name="After", value=f"`{after}`", inline=True)
                        await log_service.log_event(guild, "member", embed)
                        
                    if before.avatar != after.avatar:
                        embed = discord.Embed(title="👤 Avatar Changed", color=discord.Color.blue(), timestamp=utc_now())
                        embed.set_author(name=f"{after} ({after.id})", icon_url=after.display_avatar.url if after.display_avatar else None)
                        if before.avatar:
                            embed.add_field(name="Old Avatar", value=f"[Link]({before.avatar.url})", inline=True)
                        if after.avatar:
                            embed.set_thumbnail(url=after.avatar.url)
                        await log_service.log_event(guild, "member", embed)


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
