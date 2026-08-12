import logging
import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.security_service import SecurityService
from bot.services.log_service import LogService
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.events.member_join")

def register_member_join_event(bot: commands.Bot):
    @bot.event
    async def on_member_join(member: discord.Member):
        guild = member.guild

        async with AsyncSessionLocal() as session:
            # 1. Anti-Raid Processing
            sec_service = SecurityService(session)
            await sec_service.handle_member_join(member)

            # 2. Member Join Log
            log_service = LogService(session)
            account_age = member.created_at.strftime("%Y-%m-%d %H:%M:%S")
            embed = EmbedBuilder.info(
                title="انضمام عضو جديد (Member Joined)",
                description=f"انضم العضو {member.mention} إلى السيرفر.",
                fields=[
                    ("اسم المستخدم", f"{member} (`{member.id}`)", True),
                    ("تاريخ إنشاء الحساب", account_age, True),
                    ("عدد الأعضاء الحالي", f"`{guild.member_count}`", True)
                ]
            )
            await log_service.log_event(guild, "member", embed)

            # 3. Invite Tracking & Referral Rewards for Main Guild
            from bot.config.settings import settings
            if guild.id == settings.MAIN_GUILD_ID and not member.bot:
                try:
                    if not hasattr(bot, "invites_cache"):
                        bot.invites_cache = {}

                    cached_invites = bot.invites_cache.get(guild.id, {})
                    fresh_invites = await guild.invites()
                    used_invite = None

                    for inv in fresh_invites:
                        old_uses = cached_invites.get(inv.code, inv.uses)
                        if inv.uses > old_uses:
                            used_invite = inv
                            break

                    # Update cache
                    bot.invites_cache[guild.id] = {inv.code: inv.uses for inv in fresh_invites}

                    if used_invite and used_invite.inviter:
                        from bot.services.economy_service import EconomyService
                        eco_service = EconomyService(session)
                        await eco_service.process_invite_reward(guild, used_invite.inviter.id, member)
                except Exception as e:
                    logger.error(f"Error tracking invite for member join: {e}")
