import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.economy import UserProfile, ShopProduct, UserInventory, Wallet, Transaction
from bot.config.settings import settings
from bot.utils.time import utc_now

logger = logging.getLogger("discord_bot.profile_repository")

def calculate_level_info(total_xp: int) -> Tuple[int, int, int, float]:
    """
    Calculates (level, current_xp_in_level, needed_xp_for_next_level, progress_percentage)
    Balanced progressive RPG curve:
    Level 1: 385 XP
    Level 2: 590 XP
    Level 3: 840 XP
    Level 4: 1125 XP
    Level 5: 1445 XP
    Level 10: 3450 XP
    """
    level = 1
    accumulated = 0
    while True:
        needed = int(250 + (level * 100) + (level ** 1.6) * 35)
        if total_xp < accumulated + needed:
            current_xp = total_xp - accumulated
            progress = round((current_xp / needed) * 100, 1)
            return level, current_xp, needed, progress
        accumulated += needed
        level += 1

def generate_xp_bar(progress_percent: float, length: int = 10) -> str:
    """Generates an emoji progress bar [████░░░░░░]"""
    filled = max(0, min(length, int(round((progress_percent / 100.0) * length))))
    empty = length - filled
    return f"`[{'█' * filled}{'░' * empty}]` {progress_percent}%"

class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_profile(self, user_id: int) -> UserProfile:
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        res = await self.session.execute(stmt)
        profile = res.scalar_one_or_none()
        if not profile:
            profile = UserProfile(
                user_id=user_id,
                xp=0,
                level=1,
                bio="مرحباً بك في ملفي الشخصي!",
                bio_color="#FFFFFF",
                equipped_banner_url="https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1000&auto=format&fit=crop&q=80",
                equipped_banner_name="الافتراضي (Cosmic Default)",
                messages_count=0
            )
            self.session.add(profile)
            try:
                await self.session.flush()
                await self.session.commit()
            except Exception:
                await self.session.rollback()
        return profile

    async def add_xp(self, user_id: int, xp_amount: int, cooldown_seconds: int = 60) -> Tuple[UserProfile, bool, int]:
        """
        Adds XP to user profile with cooldown check to prevent fast level-ups.
        Returns (profile, leveled_up: bool, new_level: int)
        """
        profile = await self.get_or_create_profile(user_id)
        now = utc_now()
        profile.messages_count += 1
        
        # Check cooldown for XP gain (e.g. max once per 60 seconds)
        if profile.last_xp_at:
            elapsed = (now - profile.last_xp_at).total_seconds()
            if elapsed < cooldown_seconds:
                # User is on XP cooldown, only message count increments
                await self.session.commit()
                return profile, False, profile.level

        old_level = profile.level
        profile.xp += xp_amount
        profile.last_xp_at = now
        
        new_level, _, _, _ = calculate_level_info(profile.xp)
        leveled_up = new_level > old_level
        if leveled_up:
            profile.level = new_level

        profile.updated_at = now
        await self.session.commit()
        await self.session.refresh(profile)
        return profile, leveled_up, new_level

    async def set_custom_bio(self, user_id: int, new_bio: str, cost: int = 2000, bio_color: Optional[str] = None) -> Tuple[bool, str]:
        """
        Updates user custom bio/status and optional text color for a cost in Aura.
        """
        if len(new_bio.strip()) == 0:
            return False, "لا يمكن أن تكون الحالة فارغة!"
        if len(new_bio) > 200:
            return False, "الحالة طويلة جداً! الحد الأقصى هو 200 حرف."

        # Check and deduct balance
        stmt_w = select(Wallet).where(Wallet.user_id == user_id).with_for_update()
        res_w = await self.session.execute(stmt_w)
        wallet = res_w.scalar_one_or_none()

        if not wallet or wallet.balance < cost:
            current = wallet.balance if wallet else 0
            await self.session.rollback()
            return False, f"رصيدك الحالي (`{current}` {settings.CURRENCY_NAME}) غير كافٍ! تكلفة تغيير الحالة هي `{cost}` {settings.CURRENCY_NAME}."

        # Deduct wallet
        b_before = wallet.balance
        wallet.balance -= cost
        wallet.updated_at = utc_now()

        # Update profile
        profile = await self.get_or_create_profile(user_id)
        profile.bio = new_bio.strip()
        if bio_color:
            profile.bio_color = bio_color.strip()
        profile.updated_at = utc_now()

        # Record Transaction
        tx = Transaction(
            user_id=user_id,
            type="PROFILE_BIO",
            amount=-cost,
            balance_before=b_before,
            balance_after=wallet.balance,
            reason=f"Custom Profile Status Change"
        )
        self.session.add(tx)
        await self.session.commit()
        return True, f"تم تحديث حالتك الشخصية بنجاح وخصم `{cost}` {settings.CURRENCY_NAME}!"

    async def set_bio_color(self, user_id: int, new_color: str, cost: int = 0) -> Tuple[bool, str]:
        """Updates profile status text color."""
        profile = await self.get_or_create_profile(user_id)
        profile.bio_color = new_color.strip()
        profile.updated_at = utc_now()
        await self.session.commit()
        return True, f"تم تغيير لون نص الحالة إلى `{new_color}` بنجاح!"

    async def equip_banner(self, user_id: int, product_id: int) -> Tuple[bool, str]:
        """
        Equips a banner owned in the user inventory.
        """
        # Check if product is a banner
        stmt_p = select(ShopProduct).where(ShopProduct.product_id == product_id)
        res_p = await self.session.execute(stmt_p)
        product = res_p.scalar_one_or_none()

        if not product or product.type.upper() not in ["BANNER", "COSMETIC"]:
            return False, "هذا العنصر ليس بانر ملف شخصي!"

        # Check inventory ownership
        stmt_inv = select(UserInventory).where(
            UserInventory.user_id == user_id,
            UserInventory.product_id == product_id
        )
        res_inv = await self.session.execute(stmt_inv)
        inv = res_inv.scalar_one_or_none()

        if not inv or inv.quantity < 1:
            return False, f"أنت لا تملك بانر `{product.name}` في حقيبتك! يمكنك شراؤه من المتجر."

        profile = await self.get_or_create_profile(user_id)
        profile.equipped_banner_id = product.product_id
        profile.equipped_banner_url = product.data or "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1000&auto=format&fit=crop&q=80"
        profile.equipped_banner_name = product.name
        profile.updated_at = utc_now()

        await self.session.commit()
        return True, f"تم تجهيز بانر `{product.name}` لملفك الشخصي بنجاح!"

    async def get_user_banners(self, user_id: int) -> List[ShopProduct]:
        """Returns list of banner products the user owns"""
        stmt = select(ShopProduct).join(
            UserInventory, ShopProduct.product_id == UserInventory.product_id
        ).where(
            UserInventory.user_id == user_id,
            ShopProduct.type.in_(["BANNER", "COSMETIC"])
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_xp_leaderboard(self, limit: int = 10) -> List[UserProfile]:
        stmt = select(UserProfile).order_by(UserProfile.xp.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_user_rank(self, user_id: int) -> int:
        """Returns the global rank position of a user based on XP"""
        profile = await self.get_or_create_profile(user_id)
        stmt = select(func.count(UserProfile.user_id)).where(UserProfile.xp > profile.xp)
        res = await self.session.execute(stmt)
        higher_count = res.scalar_one() or 0
        return higher_count + 1
