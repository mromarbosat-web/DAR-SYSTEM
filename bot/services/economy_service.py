import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional, List, Dict
import discord
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config.settings import settings
from bot.database.repositories.economy_repository import EconomyRepository
from bot.services.permission_service import PermissionService
from bot.services.log_service import LogService
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.economy_service")

class EconomyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.eco_repo = EconomyRepository(session)
        self.perm_service = PermissionService(session)
        self.log_service = LogService(session)
        # In-memory cooldown tracking for message activity: {user_id: datetime}
        self._msg_cooldowns: Dict[int, datetime] = {}

    async def get_balance(self, user_id: int) -> Tuple[int, int, int]:
        wallet = await self.eco_repo.get_or_create_wallet(user_id)
        return wallet.balance, wallet.bank_balance, (wallet.balance + wallet.bank_balance)

    async def claim_daily(self, user_id: int, guild_id: Optional[int] = None) -> Tuple[bool, str, int, int]:
        es = await self.eco_repo.get_economy_settings(guild_id or settings.MAIN_GUILD_ID)
        return await self.eco_repo.claim_daily_atomic(
            user_id=user_id,
            base_reward=es.daily_reward_amount,
            streak_bonus=es.daily_streak_bonus,
            guild_id=guild_id
        )

    async def transfer_coins(
        self,
        from_user: discord.User,
        to_user: discord.User,
        amount: int,
        guild_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        if amount <= 0:
            return False, "يرجى تحديد مبلغ صحيح أكبر من 0!"
        if from_user.id == to_user.id:
            return False, "لا يمكنك تحويل النقود لنفسك!"
        if to_user.bot:
            return False, "لا يمكنك تحويل النقود للبوتات!"

        success, msg, _, _ = await self.eco_repo.transfer_balance_atomic(
            from_user_id=from_user.id,
            to_user_id=to_user.id,
            amount=amount,
            guild_id=guild_id,
            reason=f"Transfer from {from_user.name} to {to_user.name}"
        )
        return success, msg

    async def deposit(self, user_id: int, amount: int) -> Tuple[bool, str, int, int]:
        return await self.eco_repo.deposit_bank_atomic(user_id, amount)

    async def withdraw(self, user_id: int, amount: int) -> Tuple[bool, str, int, int]:
        return await self.eco_repo.withdraw_bank_atomic(user_id, amount)

    async def get_leaderboard(self, limit: int = 10, include_bank: bool = False) -> List[Tuple[int, int]]:
        return await self.eco_repo.get_leaderboard(limit=limit, include_bank=include_bank)

    async def get_average(self, include_bank: bool = False, bot_user_ids: List[int] = []) -> Tuple[int, int, float]:
        return await self.eco_repo.get_global_average(include_bank=include_bank, exclude_bot_ids=bot_user_ids)

    async def process_message_reward(self, guild_id: int, user_id: int) -> Optional[int]:
        """
        Grants message activity reward to user if guild is MAIN_GUILD_ID.
        Every 5 messages grant 1 Sarab.
        """
        if guild_id != settings.MAIN_GUILD_ID:
            return None

        es = await self.eco_repo.get_economy_settings(guild_id)
        if not es.message_rewards_enabled:
            return None

        count = self._msg_cooldowns.get(user_id, 0) + 1
        if count >= 5:
            self._msg_cooldowns[user_id] = 0
            reward = 1
            success, _, _, _ = await self.eco_repo.update_balance_atomic(
                user_id=user_id,
                amount=reward,
                transaction_type="MESSAGE_REWARD",
                guild_id=guild_id,
                reason="Message Activity Reward (5 messages)"
            )
            return reward if success else None
        else:
            self._msg_cooldowns[user_id] = count
            return None

    async def process_voice_reward(self, guild_id: int, user_id: int) -> Optional[int]:
        """
        Grants voice activity reward to user if guild is MAIN_GUILD_ID.
        """
        if guild_id != settings.MAIN_GUILD_ID:
            return None

        es = await self.eco_repo.get_economy_settings(guild_id)
        if not es.voice_rewards_enabled:
            return None

        reward = es.voice_reward_per_interval
        success, _, _, _ = await self.eco_repo.update_balance_atomic(
            user_id=user_id,
            amount=reward,
            transaction_type="VOICE_REWARD",
            guild_id=guild_id,
            reason=f"Voice Activity Reward ({es.voice_interval_minutes} mins)"
        )
        return reward if success else None

    async def process_invite_reward(
        self,
        guild: discord.Guild,
        inviter_id: int,
        invited_member: discord.Member
    ) -> Tuple[bool, str]:
        """
        Grants invite reward to inviter if guild is MAIN_GUILD_ID with strict anti-abuse checks.
        """
        if guild.id != settings.MAIN_GUILD_ID:
            return False, "مكافآت الدعوات مفعلة فقط في السيرفر الرئيسي."

        if invited_member.bot:
            return False, "لا تُمنح مكافآت مقابل دعوة البوتات."

        if inviter_id == invited_member.id:
            return False, "لا يمكن الحصول على مكافأة عن دعوة نفسك."

        # Anti-abuse 1: Account age filter (must be at least 3 days old)
        created_at = invited_member.created_at
        now = discord.utils.utcnow()
        if (now - created_at).days < 3:
            return False, "الحساب المدعو حديث جدًا (أقل من 3 أيام)، تم تجاوز المكافأة لمنع التزييف."

        # Anti-abuse 2: Has been referred check
        if await self.eco_repo.has_been_referred(invited_member.id):
            return False, "تم احتساب مكافأة هذا العضو سابقًا."

        es = await self.eco_repo.get_economy_settings(guild.id)
        if not es.invite_rewards_enabled or es.invite_reward_amount <= 0:
            return False, "مكافآت الدعوة غير مفعلة حاليًا."

        reward_amt = es.invite_reward_amount

        # Atomically give reward to inviter
        success, _, new_bal, _ = await self.eco_repo.update_balance_atomic(
            user_id=inviter_id,
            amount=reward_amt,
            transaction_type="INVITE_REWARD",
            guild_id=guild.id,
            related_user_id=invited_member.id,
            reason=f"Referral reward for inviting {invited_member} ({invited_member.id})"
        )

        if success:
            await self.eco_repo.add_referral(
                guild_id=guild.id,
                inviter_id=inviter_id,
                invited_user_id=invited_member.id,
                reward_amount=reward_amt
            )

            # Log referral event
            log_embed = EmbedBuilder.success(
                title="مكافأة دعوة عضو جديد (Invite Reward)",
                description=f"حصل الداعي <@{inviter_id}> على مكافأة قدرها `{reward_amt}` سراب لقاء دعوة {invited_member.mention}.",
                fields=[
                    ("الداعي (Inviter)", f"<@{inviter_id}> (`{inviter_id}`)", True),
                    ("العضو الجديد", f"{invited_member} (`{invited_member.id}`)", True),
                    ("المكافأة الممنوحة", f"`+{reward_amt}` {settings.CURRENCY_NAME}", True)
                ]
            )
            await self.log_service.log_event(guild, "moderation", log_embed)
            return True, f"تم إيداع `{reward_amt}` سراب لحساب الداعي بنجاح!"

        return False, "فشلت عملية إيداع مكافأة الدعوة."

    async def admin_modify_balance(
        self,
        admin_member: discord.Member,
        target_user: discord.User,
        action: str, # "give", "remove", "set", "reset"
        amount: int,
        reason: str,
        guild_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        # Permission check
        if not await self.perm_service.has_manager_permission(admin_member, "ECONOMY_MANAGER"):
            return False, "ليس لديك صلاحية إدارة الاقتصاد (`ECONOMY_MANAGER`)!"

        wallet = await self.eco_repo.get_or_create_wallet(target_user.id)
        current_bal = wallet.balance

        if action == "give":
            if amount <= 0:
                return False, "المبلغ المراد إضافته يجب أن يكون أكبر من 0!"
            change = amount
            tx_type = "ADMIN_GRANT"
        elif action == "remove":
            if amount <= 0:
                return False, "المبلغ المراد خصمه يجب أن يكون أكبر من 0!"
            if current_bal < amount:
                return False, f"رصيد العضو الحالي (`{current_bal}`) أقل من المبلغ المراد خصمه (`{amount}`)!"
            change = -amount
            tx_type = "ADMIN_REMOVE"
        elif action == "set":
            if amount < 0:
                return False, "المبلغ المثرى لا يمكن أن يكون بالسالب!"
            change = amount - current_bal
            tx_type = "ADMIN_SET"
        elif action == "reset":
            change = -current_bal
            tx_type = "ADMIN_RESET"
        else:
            return False, "نوع الإجراء الإداري غير معروف!"

        success, b_before, b_after, _ = await self.eco_repo.update_balance_atomic(
            user_id=target_user.id,
            amount=change,
            transaction_type=tx_type,
            guild_id=guild_id,
            related_user_id=admin_member.id,
            reason=f"Admin {admin_member.name} ({action}): {reason}"
        )

        if success:
            log_embed = EmbedBuilder.warning(
                title=f"تعديل إداري في الاقتصاد ({action.upper()})",
                description=f"قام الإداري {admin_member.mention} بتعديل رصيد {target_user.mention}.",
                fields=[
                    ("العضو", f"{target_user} (`{target_user.id}`)", True),
                    ("الإداري المنفذ", f"{admin_member} (`{admin_member.id}`)", True),
                    ("الرصيد السابق", f"`{b_before}` {settings.CURRENCY_NAME}", True),
                    ("الرصيد الجديد", f"`{b_after}` {settings.CURRENCY_NAME}", True),
                    ("السبب", reason, False)
                ]
            )
            if admin_member.guild:
                await self.log_service.log_event(admin_member.guild, "economy", log_embed)

            return True, f"تم تعديل رصيد {target_user.mention} بنجاح! الرصيد الجديد: `{b_after}` سراب."

        return False, "فشلت عملية التعديل الإداري للرصيد."
