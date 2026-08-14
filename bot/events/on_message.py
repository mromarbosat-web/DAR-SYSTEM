import logging
import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.automod_service import AutoModService

logger = logging.getLogger("discord_bot.events.message")

def register_message_event(bot: commands.Bot):
    @bot.event
    async def on_message(message: discord.Message):
        if not message.guild or message.author.bot:
            return

        async with AsyncSessionLocal() as session:
            automod = AutoModService(session)
            flagged = await automod.process_message(message)
            if flagged:
                return # Message deleted & handled by AutoMod

            # Process economy message reward for Main Guild
            from bot.services.economy_service import EconomyService
            from bot.services.profile_service import ProfileService
            from bot.services.activity_service import ActivityService

            # Record chat activity for Leaderboard (3-second anti-spam cooldown)
            act_service = ActivityService(session)
            await act_service.track_message_activity(message.guild.id, message.author.id, cooldown_seconds=3.0)

            eco_service = EconomyService(session)
            await eco_service.process_message_reward(message.guild.id, message.author.id)

            # Process Profile XP & Leveling
            profile_service = ProfileService(session)
            _, leveled_up, new_level = await profile_service.add_message_xp(message.author.id)
            if leveled_up:
                try:
                    await message.channel.send(
                        f"🎉 تهانينا {message.author.mention}! لقد ارتقيت إلى **المستوى {new_level}**! ⭐",
                        delete_after=10
                    )
                except Exception:
                    pass

        await bot.process_commands(message)
