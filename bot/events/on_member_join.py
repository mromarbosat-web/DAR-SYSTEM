import logging
import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.security_service import SecurityService
from bot.services.log_service import LogService
from bot.utils.embeds import EmbedBuilder
from bot.utils.time import utc_now

logger = logging.getLogger("discord_bot.events.member_join")

def register_member_join_event(bot: commands.Bot):
    @bot.event
    async def on_member_join(member: discord.Member):
        guild = member.guild
        async with AsyncSessionLocal() as session:
            # 1. Anti-Raid Processing
            sec_service = SecurityService(session)
            await sec_service.handle_member_join(member)

            # 3. Invite Tracking & Referral Rewards
            from bot.config.settings import settings
            used_invite = None
            if not member.bot:
                try:
                    if not hasattr(bot, "invites_cache"):
                        bot.invites_cache = {}
                    cached_invites = bot.invites_cache.get(guild.id, {})
                    
                    try:
                        fresh_invites = await guild.invites()
                        for inv in fresh_invites:
                            old_uses = cached_invites.get(inv.code, inv.uses)
                            if inv.uses > old_uses:
                                used_invite = inv
                                break
                        # Update cache
                        bot.invites_cache[guild.id] = {inv.code: inv.uses for inv in fresh_invites}
                    except discord.Forbidden:
                        pass # No permission to fetch invites
                        
                    if used_invite and used_invite.inviter and guild.id == settings.MAIN_GUILD_ID:
                        from bot.services.economy_service import EconomyService
                        eco_service = EconomyService(session)
                        await eco_service.process_invite_reward(guild, used_invite.inviter.id, member)
                except Exception as e:
                    logger.error(f"Error tracking invite for member join: {e}")

            # 2. Member Join Log
            log_service = LogService(session)
            
            import time
            created_at = member.created_at
            account_age = f"<t:{int(created_at.timestamp())}:R>"
            
            embed = discord.Embed(title="👤 Member Joined", color=discord.Color.green(), timestamp=utc_now())
            embed.set_author(name=f"{member} ({member.id})", icon_url=member.display_avatar.url if member.display_avatar else None)
            embed.add_field(name="Account Created", value=account_age, inline=True)
            embed.add_field(name="Member Count", value=f"`{guild.member_count}`", inline=True)
            
            if used_invite:
                inviter_str = f"{used_invite.inviter.mention} (`{used_invite.inviter.id}`)" if used_invite.inviter else "Unknown"
                embed.add_field(name="Invited By", value=inviter_str, inline=False)
                embed.add_field(name="Invite Code", value=f"`{used_invite.code}`", inline=True)
                embed.add_field(name="Uses", value=f"`{used_invite.uses - 1}` ➔ `{used_invite.uses}`", inline=True)
            else:
                # Could be a vanity URL, a bot, or a temporary invite that got deleted
                if not member.bot and 'VANITY_URL' in guild.features:
                    try:
                        vanity = await guild.vanity_invite()
                        if vanity:
                            cached_uses = bot.invites_cache.get(guild.id, {}).get(vanity.code, vanity.uses)
                            if vanity.uses > cached_uses:
                                embed.add_field(name="Invite Source", value="`Vanity URL`", inline=False)
                                bot.invites_cache[guild.id][vanity.code] = vanity.uses
                    except discord.Forbidden:
                        pass
                        
            await log_service.log_event(guild, "member", embed)
            
            if used_invite:
                await log_service.log_event(guild, "invite", embed) # Optional: Also send to invite logs

