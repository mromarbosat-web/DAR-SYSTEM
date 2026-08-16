import time
import logging
from typing import Optional, List, Dict, Tuple, Any
import discord
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories.activity_repository import ActivityRepository
from bot.database.models.economy import UserProfile
from bot.database.repositories.profile_repository import calculate_level_info
from bot.utils.leaderboard_card import generate_leaderboard_card, format_activity_score
from sqlalchemy import select

logger = logging.getLogger("discord_bot.activity_service")

# Global in-memory tracking states across session lifecycles
_MESSAGE_COOLDOWNS: Dict[int, float] = {} # user_id -> timestamp
_VOICE_SESSIONS: Dict[int, Tuple[int, float]] = {} # user_id -> (guild_id, start_time)

class ActivityService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ActivityRepository(session)

    async def track_message_activity(self, guild_id: int, user_id: int, cooldown_seconds: float = 3.0) -> bool:
        """
        Enforces a 3-second cooldown per user before recording message count into statistics.
        Returns True if the message was counted, False if throttled by cooldown.
        """
        now = time.time()
        last_time = _MESSAGE_COOLDOWNS.get(user_id, 0.0)

        if now - last_time < cooldown_seconds:
            return False

        _MESSAGE_COOLDOWNS[user_id] = now
        await self.repo.record_message(guild_id, user_id)
        return True

    async def track_voice_join(self, guild_id: int, user_id: int):
        """Marks the start timestamp for a member joining a voice channel."""
        _VOICE_SESSIONS[user_id] = (guild_id, time.time())

    async def track_voice_leave(self, guild_id: int, user_id: int) -> int:
        """
        Calculates elapsed seconds and persists them to the activity database.
        Returns the duration in seconds recorded.
        """
        session_info = _VOICE_SESSIONS.pop(user_id, None)
        if not session_info:
            return 0

        g_id, start_time = session_info
        elapsed = int(time.time() - start_time)

        if elapsed >= 1:
            await self.repo.record_voice_seconds(g_id or guild_id, user_id, elapsed)
            return elapsed
        return 0

    async def flush_active_voice_sessions(self):
        """
        Periodically called by the background voice ticker to persist elapsed time
        incrementally for members who remain connected in voice channels.
        """
        now = time.time()
        for user_id, (guild_id, start_time) in list(_VOICE_SESSIONS.items()):
            elapsed = int(now - start_time)
            if elapsed >= 30: # Flush every 30+ seconds
                _VOICE_SESSIONS[user_id] = (guild_id, now) # Reset timer
                await self.repo.record_voice_seconds(guild_id, user_id, elapsed)

    async def get_leaderboard_data(
        self,
        guild: discord.Guild,
        activity_type: str = "text",
        period: str = "daily",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetches top members strictly sorted by Level DESC, then XP DESC (tie-breaker),
        and activity score DESC, directly from the database source.
        Ranks (1..10) are assigned sequentially after strict multi-tier sorting.
        """
        raw_rows = await self.repo.get_top_leaderboard_by_level_and_xp(
            guild.id, activity_type=activity_type, period=period, limit=limit
        )
        entries: List[Dict[str, Any]] = []

        for row in raw_rows:
            user_id = row["user_id"]
            raw_xp = row.get("xp", 0)
            raw_lvl = row.get("level", 1)
            score = row.get("score", 0)

            # Re-calculate level from XP to guarantee 100% mathematical consistency
            calc_lvl, cur_xp, needed_xp, prog = calculate_level_info(raw_xp)
            final_lvl = max(raw_lvl, calc_lvl)

            member = guild.get_member(user_id)
            if member:
                name = member.name
                avatar_url = member.display_avatar.url
            else:
                name = f"User {user_id}"
                avatar_url = ""

            entries.append({
                "user_id": user_id,
                "name": name,
                "avatar_url": avatar_url,
                "score": score,
                "level": final_lvl,
                "xp": raw_xp
            })

        # Strict Multi-level Sorting:
        # 1. Level DESC
        # 2. XP DESC
        # 3. Score DESC
        entries.sort(key=lambda e: (e["level"], e["xp"], e["score"]), reverse=True)

        # Slice to requested limit (top 10)
        entries = entries[:limit]

        # Generate Rank sequentially after proper sorting
        for rank, entry in enumerate(entries, start=1):
            entry["rank"] = rank

        return entries

    async def build_leaderboard(
        self,
        guild: discord.Guild,
        activity_type: str = "text",
        period: str = "daily"
    ) -> Tuple[discord.Embed, Optional[discord.File]]:
        """
        Builds the visual leaderboard image card and interactive Discord Embed.
        """
        entries = await self.get_leaderboard_data(guild, activity_type=activity_type, period=period, limit=10)

        # Generate image card
        card_bytes = await generate_leaderboard_card(
            guild=guild,
            activity_type=activity_type,
            period=period,
            entries=entries,
            total_participants=len(entries)
        )

        period_names = {
            "daily": "📅 اليومي",
            "weekly": "📆 الأسبوعي",
            "monthly": "🗓️ الشهري",
            "all_time": "🌐 الكلي"
        }
        period_str = period_names.get(period, "📅 اليومي")

        type_names = {
            "text": "💬 الكتابة والرسائل",
            "voice": "🎙️ الرومات الصوتية"
        }
        type_str = type_names.get(activity_type, "💬 الكتابة")

        embed = discord.Embed(
            title=f"🏆 لوحة المتصدرين • {type_str} ({period_str})",
            description=f"إحصائيات أنشط الأعضاء في **{guild.name}** مرتبة حسب النشاط الفعلي والتحديث الفوري.",
            color=discord.Color.gold() if activity_type == "text" else discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )

        discord_file: Optional[discord.File] = None
        if card_bytes:
            discord_file = discord.File(fp=card_bytes, filename="leaderboard.png")
            embed.set_image(url="attachment://leaderboard.png")
        else:
            # Fallback text representation if card fails
            top_3_text = []
            for e in entries[:3]:
                medal = "🥇" if e["rank"] == 1 else ("🥈" if e["rank"] == 2 else "🥉")
                score_str = format_activity_score(activity_type, e["score"])
                top_3_text.append(f"{medal} **#{e['rank']}** <@{e['user_id']}> — Level **{e['level']}** (`{e['xp']:,}` XP) • `{score_str}`")

            if top_3_text:
                embed.add_field(name="👑 مراتب الشرف (Top 3)", value="\n".join(top_3_text), inline=False)

            remaining_text = []
            for e in entries[3:]:
                score_str = format_activity_score(activity_type, e["score"])
                remaining_text.append(f"`#{e['rank']:02d}` <@{e['user_id']}> • Level **{e['level']}** (`{e['xp']:,}` XP) • `{score_str}`")

            if remaining_text:
                embed.add_field(name="🎖️ المراكز (4 - 10)", value="\n".join(remaining_text), inline=False)
            elif not top_3_text:
                embed.description = "لا توجد إحصائيات مسجلة لهذه الفترة بعد! شارك بالرسائل أو الرومات لتتصدر القائمة."

        embed.set_footer(text=f"{guild.name} • يتم احتساب رسالة كل 3 ثوانٍ لمنع السبام", icon_url=guild.icon.url if guild.icon else None)

        return embed, discord_file
