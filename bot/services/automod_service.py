import re
import time
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import discord
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.repositories.automod_repository import AutoModRepository
from bot.database.repositories.whitelist_repository import WhitelistRepository
from bot.services.log_service import LogService
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.automod_service")

# In-memory trackers for spam
# guild_id -> user_id -> list of timestamps
user_msg_timestamps: Dict[int, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
# guild_id -> user_id -> list of (content, timestamp)
user_msg_history: Dict[int, Dict[int, List[Tuple[str, float]]]] = defaultdict(lambda: defaultdict(list))

DISCORD_INVITE_REGEX = re.compile(r"(https?://)?(www\.)?(discord\.(gg|io|me|li|com/invite)|discordapp\.com/invite)/[a-zA-Z0-9-]+")
URL_REGEX = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+")

class AutoModService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.automod_repo = AutoModRepository(session)
        self.wl_repo = WhitelistRepository(session)
        self.log_service = LogService(session)

    async def process_message(self, message: discord.Message) -> bool:
        """
        Evaluates a Discord message against AutoMod rules.
        Returns True if message was flagged and action was taken, False otherwise.
        """
        if not message.guild or message.author.bot:
            return False

        guild = message.guild
        author = message.author
        if not isinstance(author, discord.Member):
            return False

        # Load guild AutoMod settings
        settings = await self.automod_repo.get_automod_settings(guild.id)
        if not settings or not settings.enabled:
            return False

        # Check ignores (channels & roles)
        if message.channel.id in (settings.ignored_channels or []):
            return False

        user_role_ids = [r.id for r in author.roles]
        if any(rid in (settings.ignored_roles or []) for rid in user_role_ids):
            return False

        # Check global whitelist
        if await self.wl_repo.is_whitelisted(guild.id, author.id, user_role_ids):
            return False

        now = time.time()
        violation_reason = None

        # 1. Check Anti-Spam (Rapid Messages)
        if settings.anti_spam_enabled:
            timestamps = user_msg_timestamps[guild.id][author.id]
            user_msg_timestamps[guild.id][author.id] = [t for t in timestamps if now - t <= 5.0]
            user_msg_timestamps[guild.id][author.id].append(now)

            if len(user_msg_timestamps[guild.id][author.id]) > settings.max_messages_per_5s:
                violation_reason = f"سبام إرسال رسائل متكررة بسرعة ({len(user_msg_timestamps[guild.id][author.id])} رسائل خلال 5 ثوانٍ)"

        # 2. Check Duplicate Message Spam
        if not violation_reason and settings.anti_spam_enabled:
            history = user_msg_history[guild.id][author.id]
            user_msg_history[guild.id][author.id] = [h for h in history if now - h[1] <= 15.0]
            user_msg_history[guild.id][author.id].append((message.content, now))

            content_counts = sum(1 for text, _ in user_msg_history[guild.id][author.id] if text == message.content and len(text) > 3)
            if content_counts >= 3:
                violation_reason = "تكرار نفس الرسالة عدة مرات متتالية (Duplicate Message Spam)"

        # 3. Check Mass Mentions
        if not violation_reason and len(message.mentions) > settings.max_mentions:
            violation_reason = f"منشن جماعي مكثف ({len(message.mentions)} منشن)"

        # 4. Check Discord Invites
        if not violation_reason and settings.block_invites and DISCORD_INVITE_REGEX.search(message.content):
            violation_reason = "نشر روابط دعوة Discord غير مسموح بها (Discord Invite Link)"

        # 5. Check External Links
        if not violation_reason and settings.block_links and URL_REGEX.search(message.content):
            # Check if link is whitelisted
            whitelisted = False
            for w_link in (settings.whitelisted_links or []):
                if w_link and w_link.lower() in message.content.lower():
                    whitelisted = True
                    break
            if not whitelisted:
                violation_reason = "نشر روابط خارجية غير مسموح بها (External Links)"

        # 6. Check Blacklisted Words
        if not violation_reason and settings.bad_words:
            content_lower = message.content.lower()
            for bad_word in settings.bad_words:
                if bad_word and bad_word.lower() in content_lower:
                    # Check word whitelist override
                    whitelisted_word = any(
                        wl_w and wl_w.lower() in content_lower
                        for wl_w in (settings.whitelisted_words or [])
                    )
                    if not whitelisted_word:
                        violation_reason = f"استخدام كلمة محظورة ({bad_word})"
                        break

        # Handle Violation
        if violation_reason:
            try:
                await message.delete()
            except Exception as e:
                logger.error(f"Failed to delete automod message: {e}")

            # Notify user in channel briefly
            try:
                warn_msg = await message.channel.send(
                    f"⚠️ {author.mention}، تم حذف رسالتك بوسطة AutoMod! السبب: **{violation_reason}**",
                    delete_after=5
                )
            except Exception:
                pass

            # Execute configured Action
            if settings.action == "timeout":
                try:
                    await author.timeout(discord.utils.utcnow() + discord.utils.timedelta(minutes=10), reason=f"AutoMod: {violation_reason}")
                except Exception as e:
                    logger.error(f"Failed automod timeout: {e}")

            # Send Security/AutoMod Log
            embed = EmbedBuilder.warning(
                title="مخالفة AutoMod (AutoMod Violation Detected)",
                description=f"تم اكتشاف مخالفة ومعالجتها تلقائيًا من قبل نظام AutoMod.",
                fields=[
                    ("العضو المخالف", f"{author.mention} (`{author.id}`)", True),
                    ("القناة", message.channel.mention, True),
                    ("السبب", violation_reason, False),
                    ("محتوى الرسالة المحذوفة", message.content[:1000] if message.content else "*محتوى غير نصي*", False)
                ]
            )
            await self.log_service.log_event(guild, "security", embed)

            return True

        return False
