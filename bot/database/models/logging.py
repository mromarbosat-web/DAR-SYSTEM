from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.connection import Base
from bot.utils.time import utc_now

class LogSettings(Base):
    __tablename__ = "log_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), primary_key=True)
    member_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    message_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    moderation_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    role_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    channel_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    server_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    security_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)    voice_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)    invite_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)    economy_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)    verification_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)    automod_log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="log_settings")
