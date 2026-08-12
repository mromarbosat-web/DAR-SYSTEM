import logging
import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.events.member_remove")

def register_member_remove_event(bot: commands.Bot):
    @bot.event
    async def on_member_remove(member: discord.Member):
        guild = member.guild

        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            embed = EmbedBuilder.warning(
                title="مغادرة عضو (Member Left)",
                description=f"غادر العضو **{member}** السيرفر.",
                fields=[
                    ("المستخدم", f"{member} (`{member.id}`)", True),
                    ("عدد الأعضاء الحالي", f"`{guild.member_count}`", True)
                ]
            )
            await log_service.log_event(guild, "member", embed)
