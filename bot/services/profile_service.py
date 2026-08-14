import random
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
import discord
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config.settings import settings
from bot.database.repositories.profile_repository import (
    ProfileRepository, calculate_level_info, generate_xp_bar
)
from bot.database.repositories.economy_repository import EconomyRepository
from bot.database.repositories.shop_repository import ShopRepository
from bot.database.models.economy import UserProfile, ShopProduct
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.profile_service")

class ProfileService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.profile_repo = ProfileRepository(session)
        self.eco_repo = EconomyRepository(session)
        self.shop_repo = ShopRepository(session)

    async def get_profile(self, user_id: int) -> UserProfile:
        return await self.profile_repo.get_or_create_profile(user_id)

    async def add_message_xp(self, user_id: int, min_xp: int = 15, max_xp: int = 25) -> Tuple[UserProfile, bool, int]:
        """Awards message XP to user and returns (profile, leveled_up, new_level)"""
        xp_gain = random.randint(min_xp, max_xp)
        return await self.profile_repo.add_xp(user_id, xp_gain)

    async def set_bio(self, user_id: int, new_bio: str) -> Tuple[bool, str]:
        """Changes user status/bio for 2000 Aura"""
        return await self.profile_repo.set_custom_bio(user_id, new_bio, cost=2000)

    async def equip_banner(self, user_id: int, product_id: int) -> Tuple[bool, str]:
        return await self.profile_repo.equip_banner(user_id, product_id)

    async def get_user_banners(self, user_id: int) -> List[ShopProduct]:
        return await self.profile_repo.get_user_banners(user_id)

    async def build_profile_embed(self, member: discord.Member) -> discord.Embed:
        profile = await self.get_profile(member.id)
        wallet = await self.eco_repo.get_or_create_wallet(member.id)
        rank = await self.profile_repo.get_user_rank(member.id)

        level, cur_xp, needed_xp, progress = calculate_level_info(profile.xp)
        xp_bar = generate_xp_bar(progress)

        embed = discord.Embed(
            title=f"👤 الملف الشخصي | {member.display_name}",
            color=discord.Color.from_rgb(138, 43, 226)
        )
        
        # User Avatar
        embed.set_thumbnail(url=member.display_avatar.url)

        # Equipped Banner
        if profile.equipped_banner_url:
            embed.set_image(url=profile.equipped_banner_url)

        # Fields
        total_balance = wallet.balance + wallet.bank_balance
        embed.add_field(
            name="💰 رصيد الأورا (Aura Balance)",
            value=f"• المحفظة: `{wallet.balance:,}` {settings.CURRENCY_EMOJI} {settings.CURRENCY_NAME}\n• البنك: `{wallet.bank_balance:,}` {settings.CURRENCY_EMOJI}\n• الإجمالي: **`{total_balance:,}` {settings.CURRENCY_NAME}**",
            inline=False
        )

        embed.add_field(
            name="⭐ المستوى ونقاط الخبرة (Level & XP)",
            value=f"• المستوى (Level): **`{level}`**\n• الترتيب (Rank): **`#{rank}`**\n• نقاط الخبرة: `{cur_xp:,}` / `{needed_xp:,}` XP (الإجمالي: `{profile.xp:,}`)\n• التقدم: {xp_bar}",
            inline=False
        )

        embed.add_field(
            name="💬 الحالة الشخصية (Custom Status)",
            value=f"_{profile.bio}_\n*(تغيير الحالة متاح بـ 2,000 أورا)*",
            inline=False
        )

        embed.add_field(
            name="🖼️ البانر المجهز (Equipped Banner)",
            value=f"**{profile.equipped_banner_name}** *(متوفر بالمزيد في المتجر)*",
            inline=True
        )

        embed.add_field(
            name="📊 إحصائيات",
            value=f"• الرسائل: `{profile.messages_count:,}`\n• انضم في: <t:{int(member.joined_at.timestamp()) if member.joined_at else 0}:R>",
            inline=True
        )

        embed.set_footer(
            text=f"المعرف: {member.id} • Security & Aura Bot",
            icon_url=member.guild.icon.url if member.guild and member.guild.icon else None
        )

        return embed
