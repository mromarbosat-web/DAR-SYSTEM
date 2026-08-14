from datetime import date, datetime
from sqlalchemy import BigInteger, Integer, Date, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from bot.database.connection import Base
from bot.utils.time import utc_now

class MemberActivity(Base):
    """
    Tracks daily chat and voice activity per guild and member.
    Enables highly performant Daily, Weekly, Monthly, and All-Time leaderboards.
    """
    __tablename__ = "member_activity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    activity_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    messages_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    voice_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("guild_id", "user_id", "activity_date", name="uq_member_activity_guild_user_date"),
        Index("idx_activity_guild_date", "guild_id", "activity_date"),
    )
