import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple, Dict
from sqlalchemy import select, update, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils.time import utc_now

logger = logging.getLogger("discord_bot.economy_repository")

def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

class EconomyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_wallet(self, user_id: int, for_update: bool = False) -> Wallet:
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.session.execute(stmt)
        wallet = res.scalar_one_or_none()
        if not wallet:
            wallet = Wallet(user_id=user_id, balance=0, bank_balance=0)
            self.session.add(wallet)
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()
            await self.session.refresh(wallet)
        return wallet

    async def get_wallet(self, user_id: int) -> Optional[Wallet]:
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update_balance_atomic(
        self,
        user_id: int,
        amount: int,
        transaction_type: str,
        guild_id: Optional[int] = None,
        related_user_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Tuple[bool, int, int, Optional[Transaction]]:
        """
        Atomically updates wallet balance and records a transaction log.
        Amount can be positive (grant) or negative (deduct/remove).
        Returns (success: bool, balance_before: int, balance_after: int, transaction: Optional[Transaction])
        """
        async with self.session.begin_nested():
            wallet = await self.get_or_create_wallet(user_id)
            balance_before = wallet.balance
            new_balance = balance_before + amount

            if new_balance < 0:
                return False, balance_before, balance_before, None

            wallet.balance = new_balance
            wallet.updated_at = datetime.now(timezone.utc)

            tx = Transaction(
                user_id=user_id,
                guild_id=guild_id,
                type=transaction_type.upper().strip(),
                amount=amount,
                balance_before=balance_before,
                balance_after=new_balance,
                related_user_id=related_user_id,
                reason=reason
            )
            self.session.add(tx)
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()
            return True, balance_before, new_balance, tx

    async def transfer_balance_atomic(
        self,
        from_user_id: int,
        to_user_id: int,
        amount: int,
        guild_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Tuple[bool, str, int, int]:
        """
        Atomically transfers balance from_user -> to_user.
        """
        if amount <= 0:
            return False, "المبلغ يجب أن يكون أكبر من صفر!", 0, 0
        if from_user_id == to_user_id:
            return False, "لا يمكنك تحويل المبلغ لنفسك!", 0, 0

        async with self.session.begin_nested():
            sender_wallet = await self.get_or_create_wallet(from_user_id)
            receiver_wallet = await self.get_or_create_wallet(to_user_id)

            if sender_wallet.balance < amount:
                return False, "رصيدك الحالي غير كافٍ لإتمام هذه العملية!", sender_wallet.balance, receiver_wallet.balance

            s_before = sender_wallet.balance
            r_before = receiver_wallet.balance

            sender_wallet.balance -= amount
            receiver_wallet.balance += amount
            sender_wallet.updated_at = datetime.now(timezone.utc)
            receiver_wallet.updated_at = datetime.now(timezone.utc)

            # Transaction for sender
            tx_sender = Transaction(
                user_id=from_user_id,
                guild_id=guild_id,
                type="TRANSFER_OUT",
                amount=-amount,
                balance_before=s_before,
                balance_after=sender_wallet.balance,
                related_user_id=to_user_id,
                reason=reason or f"Transfer to {to_user_id}"
            )
            # Transaction for receiver
            tx_receiver = Transaction(
                user_id=to_user_id,
                guild_id=guild_id,
                type="TRANSFER_IN",
                amount=amount,
                balance_before=r_before,
                balance_after=receiver_wallet.balance,
                related_user_id=from_user_id,
                reason=reason or f"Transfer from {from_user_id}"
            )
            self.session.add_all([tx_sender, tx_receiver])
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()
            return True, "تمت عملية التحويل بنجاح!", sender_wallet.balance, receiver_wallet.balance

    async def deposit_bank_atomic(self, user_id: int, amount: int) -> Tuple[bool, str, int, int]:
        if amount <= 0:
            return False, "المبلغ يجب أن يكون أكبر من صفر!", 0, 0

        async with self.session.begin_nested():
            wallet = await self.get_or_create_wallet(user_id)
            if wallet.balance < amount:
                return False, "رصيدك في المحفظة غير كافٍ!", wallet.balance, wallet.bank_balance

            b_before = wallet.balance
            bk_before = wallet.bank_balance

            wallet.balance -= amount
            wallet.bank_balance += amount
            wallet.updated_at = datetime.now(timezone.utc)

            tx = Transaction(
                user_id=user_id,
                guild_id=None,
                type="DEPOSIT",
                amount=amount,
                balance_before=b_before,
                balance_after=wallet.balance,
                reason="Deposit to Bank"
            )
            self.session.add(tx)
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()
            return True, "تم إيداع المبلغ في البنك بنجاح!", wallet.balance, wallet.bank_balance

    async def withdraw_bank_atomic(self, user_id: int, amount: int) -> Tuple[bool, str, int, int]:
        if amount <= 0:
            return False, "المبلغ يجب أن يكون أكبر من صفر!", 0, 0

        async with self.session.begin_nested():
            wallet = await self.get_or_create_wallet(user_id)
            if wallet.bank_balance < amount:
                return False, "رصيدك في البنك غير كافٍ!", wallet.balance, wallet.bank_balance

            b_before = wallet.balance
            bk_before = wallet.bank_balance

            wallet.bank_balance -= amount
            wallet.balance += amount
            wallet.updated_at = datetime.now(timezone.utc)

            tx = Transaction(
                user_id=user_id,
                guild_id=None,
                type="WITHDRAW",
                amount=amount,
                balance_before=b_before,
                balance_after=wallet.balance,
                reason="Withdraw from Bank"
            )
            self.session.add(tx)
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()
            return True, "تم سحب المبلغ من البنك للمحفظة بنجاح!", wallet.balance, wallet.bank_balance

    async def get_daily_info(self, user_id: int) -> DailyReward:
        stmt = select(DailyReward).where(DailyReward.user_id == user_id)
        res = await self.session.execute(stmt)
        daily = res.scalar_one_or_none()
        if not daily:
            daily = DailyReward(user_id=user_id, daily_streak=0, total_claimed=0)
            self.session.add(daily)
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()
        return daily

    async def claim_daily_atomic(
        self,
        user_id: int,
        base_reward: int = 500,
        streak_bonus: int = 50,
        guild_id: Optional[int] = None
    ) -> Tuple[bool, str, int, int]:
        now = datetime.now(timezone.utc)

        async with self.session.begin_nested():
            stmt = select(DailyReward).where(DailyReward.user_id == user_id).with_for_update()
            res = await self.session.execute(stmt)
            daily = res.scalar_one_or_none()
            if not daily:
                daily = DailyReward(user_id=user_id, daily_streak=0, total_claimed=0)
                self.session.add(daily)
                await self.session.flush()

            next_daily = ensure_utc(daily.next_daily_at)
            last_daily = ensure_utc(daily.last_daily_at)

            if next_daily and now < next_daily:
                diff = next_daily - now
                total_secs = int(diff.total_seconds())
                hours, remainder = divmod(total_secs, 3600)
                minutes, seconds = divmod(remainder, 60)
                return False, f"لقد قمت بتسجيل الدخول (المكافأة اليومية) مسبقًا اليوم!\n⏳ يرجى الانتظار **{hours} ساعة، {minutes} دقيقة و {seconds} ثانية** للمطالبة بها مرة أخرى.", 0, daily.daily_streak

            # Streak calculation: if claimed within 48 hours, increase streak; otherwise reset
            if last_daily and (now - last_daily) < timedelta(hours=48):
                daily.daily_streak += 1
            else:
                daily.daily_streak = 1

            total_reward = base_reward + ((daily.daily_streak - 1) * streak_bonus)
            daily.last_daily_at = now
            daily.next_daily_at = now + timedelta(hours=24)
            daily.total_claimed += 1
            daily.updated_at = now

            # Grant reward to wallet
            wallet = await self.get_or_create_wallet(user_id)
            b_before = wallet.balance
            wallet.balance += total_reward
            wallet.updated_at = now

            tx = Transaction(
                user_id=user_id,
                guild_id=guild_id,
                type="DAILY_REWARD",
                amount=total_reward,
                balance_before=b_before,
                balance_after=wallet.balance,
                reason=f"Daily Reward (Streak {daily.daily_streak})"
            )
            self.session.add(tx)
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()

            return True, f"تم استلام المكافأة اليومية بنجاح! +{total_reward} سراب (Streak: {daily.daily_streak})", total_reward, daily.daily_streak

    async def get_leaderboard(self, limit: int = 10, include_bank: bool = False) -> List[Tuple[int, int]]:
        if include_bank:
            stmt = select(Wallet.user_id, (Wallet.balance + Wallet.bank_balance).label("total")).order_by((Wallet.balance + Wallet.bank_balance).desc()).limit(limit)
        else:
            stmt = select(Wallet.user_id, Wallet.balance).order_by(Wallet.balance.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return list(res.all())

    async def get_global_average(self, include_bank: bool = False, exclude_bot_ids: List[int] = []) -> Tuple[int, int, float]:
        """
        Returns (account_count: int, total_sarab: int, average: float)
        Excludes accounts with 0 balance or bot IDs if passed.
        """
        if include_bank:
            col = Wallet.balance + Wallet.bank_balance
        else:
            col = Wallet.balance

        stmt = select(func.count(Wallet.user_id), func.coalesce(func.sum(col), 0)).where(col > 0)
        if exclude_bot_ids:
            stmt = stmt.where(Wallet.user_id.not_in(exclude_bot_ids))

        res = await self.session.execute(stmt)
        count, total = res.one()
        count = count or 0
        total = total or 0
        avg = (total / count) if count > 0 else 0.0
        return count, total, avg

    async def get_economy_settings(self, guild_id: int) -> EconomySettings:
        stmt = select(EconomySettings).where(EconomySettings.guild_id == guild_id)
        res = await self.session.execute(stmt)
        es = res.scalar_one_or_none()
        if not es:
            es = EconomySettings(guild_id=guild_id)
            self.session.add(es)
            await self.session.flush()
        return es

    async def update_economy_settings(self, guild_id: int, **kwargs) -> EconomySettings:
        es = await self.get_economy_settings(guild_id)
        for key, value in kwargs.items():
            if hasattr(es, key) and value is not None:
                setattr(es, key, value)
        es.updated_at = utc_now()
        await self.session.flush()
        return es

    async def add_referral(self, guild_id: int, inviter_id: int, invited_user_id: int, reward_amount: int) -> Referral:
        ref = Referral(
            guild_id=guild_id,
            inviter_id=inviter_id,
            invited_user_id=invited_user_id,
            reward_amount=reward_amount,
            rewarded=True
        )
        self.session.add(ref)
        await self.session.flush()
        return ref

    async def has_been_referred(self, invited_user_id: int) -> bool:
        stmt = select(Referral).where(Referral.invited_user_id == invited_user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none() is not None
