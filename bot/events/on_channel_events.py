import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.time import utc_now

def register_channel_logs_events(bot: commands.Bot):
    @bot.event
    async def on_guild_channel_create(channel: discord.abc.GuildChannel):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            embed = discord.Embed(title="📁 Channel Created", color=discord.Color.green(), timestamp=utc_now())
            embed.add_field(name="Channel", value=f"{channel.mention} (`{channel.name}`)", inline=False)
            embed.add_field(name="Type", value=f"`{channel.type}`", inline=True)
            if hasattr(channel, "category") and channel.category:
                embed.add_field(name="Category", value=f"`{channel.category.name}`", inline=True)
            embed.set_footer(text=f"Channel ID: {channel.id}")
            await log_service.log_event(channel.guild, "channel", embed)

    @bot.event
    async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            embed = discord.Embed(title="📁 Channel Deleted", color=discord.Color.red(), timestamp=utc_now())
            embed.add_field(name="Channel", value=f"`{channel.name}`", inline=False)
            embed.add_field(name="Type", value=f"`{channel.type}`", inline=True)
            embed.set_footer(text=f"Channel ID: {channel.id}")
            await log_service.log_event(channel.guild, "channel", embed)

    @bot.event
    async def on_guild_channel_update(before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            changes = []
            if before.name != after.name:
                changes.append(f"**Name:** `{before.name}` ➔ `{after.name}`")
            if hasattr(before, "topic") and hasattr(after, "topic") and before.topic != after.topic:
                b_topic = str(before.topic)[:100] if before.topic else "None"
                a_topic = str(after.topic)[:100] if after.topic else "None"
                changes.append(f"**Topic:** `{b_topic}` ➔ `{a_topic}`")
            if hasattr(before, "slowmode_delay") and hasattr(after, "slowmode_delay") and before.slowmode_delay != after.slowmode_delay:
                changes.append(f"**Slowmode:** `{before.slowmode_delay}s` ➔ `{after.slowmode_delay}s`")
            if hasattr(before, "nsfw") and hasattr(after, "nsfw") and before.nsfw != after.nsfw:
                changes.append(f"**NSFW:** `{before.nsfw}` ➔ `{after.nsfw}`")
            if getattr(before, "category_id", None) != getattr(after, "category_id", None):
                b_cat = before.category.name if getattr(before, "category", None) else "None"
                a_cat = after.category.name if getattr(after, "category", None) else "None"
                changes.append(f"**Category:** `{b_cat}` ➔ `{a_cat}`")
                
            if not changes:
                return # Likely permission overwrites which we don't log explicitly here, or unhandled
                
            embed = discord.Embed(title="📁 Channel Updated", description="\n".join(changes), color=discord.Color.gold(), timestamp=utc_now())
            embed.add_field(name="Channel", value=f"{after.mention} (`{after.name}`)", inline=False)
            embed.set_footer(text=f"Channel ID: {after.id}")
            await log_service.log_event(after.guild, "channel", embed)

