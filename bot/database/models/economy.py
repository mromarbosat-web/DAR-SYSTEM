from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import BigInteger, String, Boolean, DateTime, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.connection import Base

class Wallet(Base):
    __tablename__ = "wallets"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True, index=True)
    balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    bank_balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class DailyReward(Base):
    __tablename__ = "daily_rewards"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    last_daily_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    next_daily_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    daily_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_claimed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_before: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_after: Mapped[int] = mapped_column(BigInteger, nullable=False)
    related_user_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

class EconomySettings(Base):
    __tablename__ = "economy_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    currency_name: Mapped[str] = mapped_column(String(50), default="أروا", nullable=False)
    currency_emoji: Mapped[str] = mapped_column(String(50), default="✨", nullable=False)
    daily_reward_amount: Mapped[int] = mapped_column(BigInteger, default=500, nullable=False)
    daily_streak_bonus: Mapped[int] = mapped_column(BigInteger, default=50, nullable=False)
    invite_reward_amount: Mapped[int] = mapped_column(BigInteger, default=100, nullable=False)
    message_reward_min: Mapped[int] = mapped_column(BigInteger, default=10, nullable=False)
    message_reward_max: Mapped[int] = mapped_column(BigInteger, default=25, nullable=False)
    message_cooldown_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    voice_reward_per_interval: Mapped[int] = mapped_column(BigInteger, default=30, nullable=False)
    voice_interval_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    message_rewards_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    voice_rewards_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    invite_rewards_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True, index=True)
    xp: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    bio: Mapped[str] = mapped_column(String(300), default="مرحباً بك في ملفي الشخصي!", nullable=False)
    bio_color: Mapped[Optional[str]] = mapped_column(String(50), default="#FFFFFF", nullable=True)
    equipped_banner_id: Mapped[int] = mapped_column(Integer, ForeignKey("shop_products.product_id", ondelete="SET NULL"), nullable=True)
    equipped_banner_url: Mapped[str] = mapped_column(String(500), nullable=True)
    equipped_banner_name: Mapped[str] = mapped_column(String(100), default="الافتراضي", nullable=False)
    messages_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_xp_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ShopProduct(Base):
    __tablename__ = "shop_products"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    emoji: Mapped[str] = mapped_column(String(50), default="📦", nullable=True)
    stock: Mapped[int] = mapped_column(Integer, default=-1, nullable=False)  # -1 means unlimited
    max_per_user: Mapped[int] = mapped_column(Integer, default=-1, nullable=False)  # -1 means unlimited
    type: Mapped[str] = mapped_column(String(50), default="ROLE", nullable=False)  # ROLE, ITEM, COLOR, COSMETIC, ACCESS
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    data: Mapped[str] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class UserInventory(Base):
    __tablename__ = "user_inventory"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product_inventory"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("shop_products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    inviter_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    invited_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reward_amount: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    rewarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
