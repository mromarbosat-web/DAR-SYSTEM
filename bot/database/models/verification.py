from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.connection import Base

class VerificationSettings(Base):
    __tablename__ = "verification_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    verified_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    unverified_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    panel_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    title: Mapped[str] = mapped_column(String(255), default="نظام التحقق - Verification System")
    description: Mapped[str] = mapped_column(Text, default="اضغط على الزر أدناه لإكمال عملية التحقق والحصول على الرتبة.")
    button_text: Mapped[str] = mapped_column(String(100), default="تحقق الآن / Verify")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="verification_settings")
