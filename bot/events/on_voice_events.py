import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.time import utc_now

def register_voice_logs_events(bot: commands.Bot):
    @bot.event
    async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.guild is None:
            return
            
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            # Voice Join
            if before.channel is None and after.channel is not None:
                embed = discord.Embed(title="🔊 Voice Join", color=discord.Color.green(), timestamp=utc_now())
                embed.set_author(name=f"{member} ({member.id})", icon_url=member.display_avatar.url if member.display_avatar else None)
                embed.add_field(name="Channel", value=f"{after.channel.mention} (`{after.channel.id}`)", inline=False)
                await log_service.log_event(member.guild, "voice", embed)
                
            # Voice Leave
            elif before.channel is not None and after.channel is None:
                embed = discord.Embed(title="🔇 Voice Leave", color=discord.Color.red(), timestamp=utc_now())
                embed.set_author(name=f"{member} ({member.id})", icon_url=member.display_avatar.url if member.display_avatar else None)
                embed.add_field(name="Channel", value=f"{before.channel.mention} (`{before.channel.id}`)", inline=False)
                await log_service.log_event(member.guild, "voice", embed)
                
            # Voice Move
            elif before.channel != after.channel:
                embed = discord.Embed(title="🔄 Voice Move", color=discord.Color.blue(), timestamp=utc_now())
                embed.set_author(name=f"{member} ({member.id})", icon_url=member.display_avatar.url if member.display_avatar else None)
                embed.add_field(name="From", value=f"{before.channel.mention} (`{before.channel.id}`)", inline=True)
                embed.add_field(name="To", value=f"{after.channel.mention} (`{after.channel.id}`)", inline=True)
                await log_service.log_event(member.guild, "voice", embed)
                
            # Mute/Unmute (Server)
            if before.mute != after.mute:
                action = "Server Muted" if after.mute else "Server Unmuted"
                embed = discord.Embed(title=f"🎤 {action}", color=discord.Color.orange(), timestamp=utc_now())
                embed.set_author(name=f"{member} ({member.id})", icon_url=member.display_avatar.url if member.display_avatar else None)
                if after.channel:
                    embed.add_field(name="Channel", value=f"{after.channel.mention} (`{after.channel.id}`)", inline=False)
                await log_service.log_event(member.guild, "voice", embed)
                
            # Deafen/Undeafen (Server)
            if before.deaf != after.deaf:
                action = "Server Deafened" if after.deaf else "Server Undeafened"
                embed = discord.Embed(title=f"🎧 {action}", color=discord.Color.orange(), timestamp=utc_now())
                embed.set_author(name=f"{member} ({member.id})", icon_url=member.display_avatar.url if member.display_avatar else None)
                if after.channel:
                    embed.add_field(name="Channel", value=f"{after.channel.mention} (`{after.channel.id}`)", inline=False)
                await log_service.log_event(member.guild, "voice", embed)

            # Self Mute/Unmute
            if before.self_mute != after.self_mute:
                action = "Self Muted" if after.self_mute else "Self Unmuted"
                embed = discord.Embed(title=f"🎤 {action}", color=discord.Color.light_grey(), timestamp=utc_now())
                embed.set_author(name=f"{member} ({member.id})", icon_url=member.display_avatar.url if member.display_avatar else None)
                if after.channel:
                    embed.add_field(name="Channel", value=f"{after.channel.mention} (`{after.channel.id}`)", inline=False)
                await log_service.log_event(member.guild, "voice", embed)
                
            # Stream start/stop
            if before.self_stream != after.self_stream:
                action = "Started Streaming" if after.self_stream else "Stopped Streaming"
                embed = discord.Embed(title=f"📺 {action}", color=discord.Color.purple(), timestamp=utc_now())
                embed.set_author(name=f"{member} ({member.id})", icon_url=member.display_avatar.url if member.display_avatar else None)
                if after.channel:
                    embed.add_field(name="Channel", value=f"{after.channel.mention} (`{after.channel.id}`)", inline=False)
                await log_service.log_event(member.guild, "voice", embed)

