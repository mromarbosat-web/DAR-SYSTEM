import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import BigInteger, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.connection import Base
from bot.utils.time import utc_now

class WarningSettings(Base):
    __tablename__ = "warning_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), primary_key=True)
    issuer_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    viewer_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    editor_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    remover_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    expirer_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    evidence_manager_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    settings_manager_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    evidence_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    default_warning_duration: Mapped[str] = mapped_column(String(50), default="30d")
    staff_demotion_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    staff_demotion_threshold: Mapped[int] = mapped_column(Integer, default=3)
    demotion_action: Mapped[str] = mapped_column(String(50), default="remove_roles") # remove_roles, timeout, kick
    verbal_warning_threshold: Mapped[int] = mapped_column(Integer, default=3)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="warning_settings")

class Warning(Base):
    __tablename__ = "warnings"

    warning_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    moderator_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    warning_type: Mapped[str] = mapped_column(String(20), default="formal", nullable=False) # formal, verbal
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False) # ACTIVE, EXPIRED, REMOVED, VOIDED
    
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    duration_seconds: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True) # None = Permanent
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    edited_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    edit_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON list
    
    removed_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    removal_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    evidences: Mapped[List["WarningEvidence"]] = relationship("WarningEvidence", back_populates="warning", cascade="all, delete-orphan")

class WarningEvidence(Base):
    __tablename__ = "warning_evidence"

    evidence_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    warning_id: Mapped[str] = mapped_column(String(36), ForeignKey("warnings.warning_id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_url: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    warning: Mapped["Warning"] = relationship("Warning", back_populates="evidences")
