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
