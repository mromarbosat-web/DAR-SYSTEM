from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import BigInteger, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from bot.database.connection import Base
from bot.utils.time import utc_now

class CommandShortcut(Base):
    __tablename__ = "command_shortcuts"
    __table_args__ = (
        UniqueConstraint("guild_id", "trigger_word", name="uq_guild_trigger_word"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_word: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_action: Mapped[str] = mapped_column(String(50), nullable=False) # warn, timeout, kick, ban, purge, lock, unlock, voice_mute, voice_disconnect, voice_move, profile, balance, shop, daily, warnings
    allowed_roles: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # comma-separated role IDs
    allowed_users: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # comma-separated user IDs
    allowed_channels: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # comma-separated channel IDs
    ignored_channels: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # comma-separated channel IDs
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
