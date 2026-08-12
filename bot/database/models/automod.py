from datetime import datetime
from typing import List
from sqlalchemy import BigInteger, String, Boolean, Integer, DateTime, ForeignKey, ARRAY, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.connection import Base

class AutoModSettings(Base):
    __tablename__ = "automod_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), primary_key=True)
    
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_spam_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    max_messages_per_5s: Mapped[int] = mapped_column(Integer, default=5)
    max_mentions: Mapped[int] = mapped_column(Integer, default=5)
    block_invites: Mapped[bool] = mapped_column(Boolean, default=True)
    block_links: Mapped[bool] = mapped_column(Boolean, default=False)
    
    bad_words: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    whitelisted_words: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    whitelisted_links: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    ignored_channels: Mapped[List[int]] = mapped_column(ARRAY(BigInteger), default=list)
    ignored_roles: Mapped[List[int]] = mapped_column(ARRAY(BigInteger), default=list)
    
    action: Mapped[str] = mapped_column(String(50), default="delete_and_warn") # delete_and_warn, timeout, kick
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="automod_settings")
