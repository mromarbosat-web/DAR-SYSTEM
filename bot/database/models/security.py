from datetime import datetime
from sqlalchemy import BigInteger, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.connection import Base

class SecuritySettings(Base):
    __tablename__ = "security_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), primary_key=True)
    
    # Anti-Raid Settings
    anti_raid_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_raid_join_threshold: Mapped[int] = mapped_column(Integer, default=5)
    anti_raid_time_window: Mapped[int] = mapped_column(Integer, default=10) # Seconds
    anti_raid_action: Mapped[str] = mapped_column(String(50), default="lockdown") # lockdown, kick, ban, timeout
    
    # Anti-Nuke Settings
    anti_nuke_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_nuke_channel_threshold: Mapped[int] = mapped_column(Integer, default=3)
    anti_nuke_role_threshold: Mapped[int] = mapped_column(Integer, default=3)
    anti_nuke_time_window: Mapped[int] = mapped_column(Integer, default=10) # Seconds
    anti_nuke_action: Mapped[str] = mapped_column(String(50), default="remove_roles") # remove_roles, ban, timeout
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="security_settings")
