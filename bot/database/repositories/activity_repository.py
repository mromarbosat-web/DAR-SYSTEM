import logging
from datetime import date, datetime, timedelta
from typing import List, Tuple, Optional, Dict
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.activity import MemberActivity
from bot.utils.time import utc_now

logger = logging.getLogger("discord_bot.activity_repository")

class ActivityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_message(self, guild_id: int, user_id: int) -> None:
        """
        Atomically records a message count for the user for today's date.
        Uses PostgreSQL ON CONFLICT upsert.
        """
        try:
            today = date.today()
            stmt = text("""
                INSERT INTO member_activity (guild_id, user_id, activity_date, messages_count, voice_seconds, created_at, updated_at)
                VALUES (:guild_id, :user_id, :activity_date, 1, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (guild_id, user_id, activity_date)
                DO UPDATE SET 
                    messages_count = member_activity.messages_count + 1,
                    updated_at = CURRENT_TIMESTAMP;
            """)
            await self.session.execute(stmt, {
                "guild_id": guild_id,
                "user_id": user_id,
                "activity_date": today
            })
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to record message activity for user {user_id}: {e}")

    async def record_voice_seconds(self, guild_id: int, user_id: int, seconds: int) -> None:
        """
        Atomically records voice time (in seconds) for the user for today's date.
        """
        if seconds <= 0:
            return
        try:
            today = date.today()
            stmt = text("""
                INSERT INTO member_activity (guild_id, user_id, activity_date, messages_count, voice_seconds, created_at, updated_at)
                VALUES (:guild_id, :user_id, :activity_date, 0, :seconds, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (guild_id, user_id, activity_date)
                DO UPDATE SET 
                    voice_seconds = member_activity.voice_seconds + :seconds,
                    updated_at = CURRENT_TIMESTAMP;
            """)
            await self.session.execute(stmt, {
                "guild_id": guild_id,
                "user_id": user_id,
                "activity_date": today,
                "seconds": seconds
            })
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to record voice activity for user {user_id}: {e}")

    async def get_top_leaderboard(
        self,
        guild_id: int,
        activity_type: str = "text",
        period: str = "daily",
        limit: int = 10
    ) -> List[Tuple[int, int]]:
        """
        Retrieves top members ranked by activity for the requested period.
        
        activity_type: 'text' (messages) or 'voice' (seconds)
        period: 'daily', 'weekly', 'monthly', 'all_time'
        
        Returns: List of tuples (user_id, total_score)
        """
        try:
            col_name = "messages_count" if activity_type == "text" else "voice_seconds"
            today = date.today()

            date_clause = ""
            params: Dict[str, object] = {"guild_id": guild_id, "limit": limit}

            if period == "daily":
                date_clause = "AND activity_date = :start_date"
                params["start_date"] = today
            elif period == "weekly":
                date_clause = "AND activity_date >= :start_date"
                params["start_date"] = today - timedelta(days=6)
            elif period == "monthly":
                date_clause = "AND activity_date >= :start_date"
                params["start_date"] = today - timedelta(days=29)
            elif period == "all_time":
                date_clause = ""

            sql = f"""
                SELECT user_id, SUM({col_name}) AS total_score
                FROM member_activity
                WHERE guild_id = :guild_id {date_clause}
                GROUP BY user_id
                HAVING SUM({col_name}) > 0
                ORDER BY total_score DESC
                LIMIT :limit;
            """
            
            result = await self.session.execute(text(sql), params)
            rows = result.all()
            return [(int(r[0]), int(r[1])) for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch leaderboard for {activity_type}/{period}: {e}")
            return []

    async def get_user_rank_and_score(
        self,
        guild_id: int,
        user_id: int,
        activity_type: str = "text",
        period: str = "daily"
    ) -> Tuple[int, int]:
        """
        Returns (rank, score) for a specific user.
        If user has no activity, returns (0, 0).
        """
        try:
            col_name = "messages_count" if activity_type == "text" else "voice_seconds"
            today = date.today()

            date_clause = ""
            params: Dict[str, object] = {"guild_id": guild_id, "user_id": user_id}

            if period == "daily":
                date_clause = "AND activity_date = :start_date"
                params["start_date"] = today
            elif period == "weekly":
                date_clause = "AND activity_date >= :start_date"
                params["start_date"] = today - timedelta(days=6)
            elif period == "monthly":
                date_clause = "AND activity_date >= :start_date"
                params["start_date"] = today - timedelta(days=29)

            sql = f"""
                WITH ranked AS (
                    SELECT 
                        user_id, 
                        SUM({col_name}) AS total_score,
                        ROW_NUMBER() OVER (ORDER BY SUM({col_name}) DESC) AS rank_pos
                    FROM member_activity
                    WHERE guild_id = :guild_id {date_clause}
                    GROUP BY user_id
                    HAVING SUM({col_name}) > 0
                )
                SELECT rank_pos, total_score FROM ranked WHERE user_id = :user_id;
            """
            result = await self.session.execute(text(sql), params)
            row = result.first()
            if row:
                return (int(row[0]), int(row[1]))
            return (0, 0)
        except Exception as e:
            logger.error(f"Failed to fetch user rank for {user_id}: {e}")
            return (0, 0)
