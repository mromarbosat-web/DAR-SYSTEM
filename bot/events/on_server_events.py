import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.time import utc_now
from bot.config.settings import settings
from bot.utils.logger import logger

def register_server_logs_events(bot: commands.Bot):
    @bot.event
    async def on_guild_update(before: discord.Guild, after: discord.Guild):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            changes = []
            if before.name != after.name:
                changes.append(f"**Name:** `{before.name}` ➔ `{after.name}`")
            if before.verification_level != after.verification_level:
                changes.append(f"**Verification Level:** `{before.verification_level.name}` ➔ `{after.verification_level.name}`")
            if before.vanity_url_code != after.vanity_url_code:
                changes.append(f"**Vanity URL:** `{before.vanity_url_code}` ➔ `{after.vanity_url_code}`")
            
            if changes:
                embed = discord.Embed(title="⚙️ Server Settings Updated", description="\n".join(changes), color=discord.Color.purple(), timestamp=utc_now())
                embed.set_thumbnail(url=after.icon.url if after.icon else None)
                await log_service.log_event(after, "server", embed)
                
            if before.icon != after.icon:
                embed = discord.Embed(title="⚙️ Server Icon Updated", color=discord.Color.purple(), timestamp=utc_now())
                if before.icon:
                    embed.add_field(name="Old Icon", value=f"[Link]({before.icon.url})", inline=True)
                if after.icon:
                    embed.set_thumbnail(url=after.icon.url)
                await log_service.log_event(after, "server", embed)

            if before.banner != after.banner:
                embed = discord.Embed(title="⚙️ Server Banner Updated", color=discord.Color.purple(), timestamp=utc_now())
                if before.banner:
                    embed.add_field(name="Old Banner", value=f"[Link]({before.banner.url})", inline=True)
                if after.banner:
                    embed.set_image(url=after.banner.url)
                await log_service.log_event(after, "server", embed)

    @bot.event
    async def on_invite_create(invite: discord.Invite):
        # Update cache
        if hasattr(bot, "invites_cache") and invite.guild.id in bot.invites_cache:
            bot.invites_cache[invite.guild.id][invite.code] = invite.uses
            
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            embed = discord.Embed(title="🔗 Invite Created", color=discord.Color.green(), timestamp=utc_now())
            inviter = invite.inviter
            if inviter:
                embed.set_author(name=f"{inviter} ({inviter.id})", icon_url=inviter.display_avatar.url if inviter.display_avatar else None)
            embed.add_field(name="Code", value=f"`{invite.code}`", inline=True)
            embed.add_field(name="Channel", value=f"{invite.channel.mention}", inline=True)
            if invite.max_uses > 0:
                embed.add_field(name="Max Uses", value=f"`{invite.max_uses}`", inline=True)
            if invite.max_age > 0:
                embed.add_field(name="Max Age", value=f"`{invite.max_age}s`", inline=True)
            await log_service.log_event(invite.guild, "invite", embed)

    @bot.event
    async def on_invite_delete(invite: discord.Invite):
        # Update cache
        if hasattr(bot, "invites_cache") and invite.guild.id in bot.invites_cache:
            if invite.code in bot.invites_cache[invite.guild.id]:
                del bot.invites_cache[invite.guild.id][invite.code]
                
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            embed = discord.Embed(title="🔗 Invite Deleted", color=discord.Color.red(), timestamp=utc_now())
            embed.add_field(name="Code", value=f"`{invite.code}`", inline=True)
            embed.add_field(name="Channel", value=f"{invite.channel.mention}", inline=True)
            await log_service.log_event(invite.guild, "invite", embed)

