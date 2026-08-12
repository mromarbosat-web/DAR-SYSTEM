from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.connection import Base

class LogSettings(Base):
    __tablename__ = "log_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), primary_key=True)
    member_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    message_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    moderation_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    role_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    channel_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    server_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    security_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="log_settings")
