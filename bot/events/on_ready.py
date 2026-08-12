import logging
import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.verification_service import VerificationView

logger = logging.getLogger("discord_bot.events.ready")

def register_ready_event(bot: commands.Bot):
    @bot.event
    async def on_ready():
        logger.info(f"Bot logged in successfully as {bot.user} (ID: {bot.user.id})")
        logger.info(f"Connected to {len(bot.guilds)} Discord guilds.")

        # Reconnect guard: Only sync slash commands and register views on first ready
        if not getattr(bot, "_has_initialized_on_ready", False):
            bot._has_initialized_on_ready = True

            # Register persistent Verification Button View
            try:
                bot.add_view(VerificationView(AsyncSessionLocal))
                logger.info("Persistent Verification Button View registered.")
            except Exception as e:
                logger.error(f"Error registering Verification persistent view: {e}")

            # Cache invites for Main Guild
            from bot.config.settings import settings
            if not hasattr(bot, "invites_cache"):
                bot.invites_cache = {}

            main_guild = bot.get_guild(settings.MAIN_GUILD_ID)
            if main_guild:
                try:
                    invites = await main_guild.invites()
                    bot.invites_cache[main_guild.id] = {inv.code: inv.uses for inv in invites}
                    logger.info(f"Initialized invite cache for Main Guild ({main_guild.id}): {len(invites)} invites cached.")
                except Exception as e:
                    logger.error(f"Failed to initialize invite cache: {e}")

            # Start Voice Rewards Ticker Loop Task
            if not getattr(bot, "_voice_rewards_task_started", False):
                bot._voice_rewards_task_started = True
                bot.loop.create_task(voice_rewards_ticker(bot))

            # Sync Slash Commands with Discord Gateway
            try:
                synced = await bot.tree.sync()
                logger.info(f"Successfully synced {len(synced)} application slash commands globally.")
            except Exception as e:
                logger.error(f"Error syncing application slash commands: {e}")

        # Set Activity Status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Shielding Servers • /security"
        )
        await bot.change_presence(activity=activity, status=discord.Status.online)

async def voice_rewards_ticker(bot: commands.Bot):
    """
    Background task checking voice activity in MAIN_GUILD_ID every 60 seconds.
    Tracks active minutes for eligible unmuted/undeafened members in active voice channels.
    """
    import asyncio
    from bot.config.settings import settings
    from bot.services.economy_service import EconomyService

    member_voice_minutes = {}

    while not bot.is_closed():
        await asyncio.sleep(60)
        try:
            guild = bot.get_guild(settings.MAIN_GUILD_ID)
            if not guild:
                continue

            async with AsyncSessionLocal() as session:
                eco_service = EconomyService(session)
                es = await eco_service.eco_repo.get_economy_settings(guild.id)
                if not es.voice_rewards_enabled:
                    continue

                interval_mins = es.voice_interval_minutes or 5

                for vc in guild.voice_channels:
                    # Ignore AFK channel
                    if guild.afk_channel and vc.id == guild.afk_channel.id:
                        continue

                    # Filter eligible members (non-bots, at least 2 non-bots in channel)
                    human_members = [m for m in vc.members if not m.bot]
                    if len(human_members) < 2:
                        continue

                    for member in human_members:
                        vstate = member.voice
                        if not vstate:
                            continue
                        if vstate.self_mute or vstate.mute or vstate.self_deaf or vstate.deaf:
                            continue

                        cnt = member_voice_minutes.get(member.id, 0) + 1
                        if cnt >= interval_mins:
                            member_voice_minutes[member.id] = 0
                            await eco_service.process_voice_reward(guild.id, member.id)
                        else:
                            member_voice_minutes[member.id] = cnt
        except Exception as e:
            logger.error(f"Error in voice rewards ticker: {e}")
