from datetime import datetime
from sqlalchemy import BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.connection import Base

class Guild(Base):
    __tablename__ = "guilds"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    settings: Mapped["GuildSettings"] = relationship("GuildSettings", back_populates="guild", uselist=False, cascade="all, delete-orphan")
    security_settings: Mapped["SecuritySettings"] = relationship("SecuritySettings", back_populates="guild", uselist=False, cascade="all, delete-orphan")
    automod_settings: Mapped["AutoModSettings"] = relationship("AutoModSettings", back_populates="guild", uselist=False, cascade="all, delete-orphan")
    verification_settings: Mapped["VerificationSettings"] = relationship("VerificationSettings", back_populates="guild", uselist=False, cascade="all, delete-orphan")
    log_settings: Mapped["LogSettings"] = relationship("LogSettings", back_populates="guild", uselist=False, cascade="all, delete-orphan")
    punishment_settings: Mapped["PunishmentSettings"] = relationship("PunishmentSettings", back_populates="guild", uselist=False, cascade="all, delete-orphan")
    warning_settings: Mapped["WarningSettings"] = relationship("WarningSettings", back_populates="guild", uselist=False, cascade="all, delete-orphan")
    voice_settings: Mapped["VoiceSettings"] = relationship("VoiceSettings", back_populates="guild", uselist=False, cascade="all, delete-orphan")

class GuildSettings(Base):
    __tablename__ = "guild_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), primary_key=True)
    prefix: Mapped[str] = mapped_column(String(10), default="!")
    language: Mapped[str] = mapped_column(String(10), default="ar")
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="settings")
