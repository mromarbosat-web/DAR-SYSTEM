import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.connection import Base

class PunishmentSettings(Base):
    __tablename__ = "punishment_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), primary_key=True)
    warn_3_action: Mapped[str] = mapped_column(String(50), default="timeout_1h") # timeout_1h, kick, ban, none
    warn_5_action: Mapped[str] = mapped_column(String(50), default="kick")
    warn_7_action: Mapped[str] = mapped_column(String(50), default="ban")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="punishment_settings")

class ModerationAction(Base):
    __tablename__ = "moderation_actions"

    action_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    moderator_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False) # warn, timeout, kick, ban, unban, softban, purge, lock, unlock
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # duration in seconds
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
