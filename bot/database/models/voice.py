import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.connection import Base
from bot.utils.time import utc_now

class VoiceSettings(Base):
    __tablename__ = "voice_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), primary_key=True)
    voice_manager_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    voice_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="voice_settings")

class VoiceActionLog(Base):
    __tablename__ = "voice_action_logs"

    log_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), nullable=False, index=True)
    executor_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    target_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True) # None for channel operations
    action_type: Mapped[str] = mapped_column(String(50), nullable=False) # move, disconnect, mute, unmute, lock, unlock
    channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    target_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
