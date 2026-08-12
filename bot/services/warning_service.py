import re
import discord
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.repositories.warning_repository import WarningRepository
from bot.database.repositories.log_repository import LogRepository
from bot.database.models import Warning, WarningSettings, WarningEvidence
from bot.utils.logger import logger

def parse_duration_string(duration_str: str) -> Tuple[Optional[int], Optional[datetime]]:
    """
    Parses duration string like '1h', '1d', '1w', '1m', '3m', '6m', '1y', 'permanent', '0'
    Returns (duration_seconds, expires_at)
    """
    if not duration_str or duration_str.lower() in ["permanent", "perm", "0", "forever", "دائم", "دائمة"]:
        return None, None

    match = re.match(r"^(\d+)\s*([hdwmy])$", duration_str.lower().strip())
    if not match:
        # Default to 30 days if invalid pattern
        delta = timedelta(days=30)
        return int(delta.total_seconds()), datetime.utcnow() + delta

    val = int(match.group(1))
    unit = match.group(2)

    if unit == "h":
        delta = timedelta(hours=val)
    elif unit == "d":
        delta = timedelta(days=val)
    elif unit == "w":
        delta = timedelta(weeks=val)
    elif unit == "m":
        delta = timedelta(days=val * 30)
    elif unit == "y":
        delta = timedelta(days=val * 365)
    else:
        delta = timedelta(days=30)

    total_seconds = int(delta.total_seconds())
    expires_at = datetime.utcnow() + delta
    return total_seconds, expires_at

class WarningService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.warning_repo = WarningRepository(session)
        self.log_repo = LogRepository(session)

    async def get_settings(self, guild_id: int) -> WarningSettings:
        return await self.warning_repo.get_or_create_warning_settings(guild_id)

    async def update_settings(self, guild_id: int, **kwargs) -> WarningSettings:
        return await self.warning_repo.update_warning_settings(guild_id, **kwargs)

    async def issue_warning(
        self,
        guild: discord.Guild,
        issuer: discord.Member,
        target: discord.Member,
        reason: str,
        warning_type: str = "formal",
        duration_str: Optional[str] = None,
        evidence_url: Optional[str] = None
    ) -> Tuple[Warning, Optional[str]]:
        """
        Issues a warning and checks for demotion thresholds.
        Returns (Warning, punishment_triggered_msg)
        """
        settings = await self.get_settings(guild.id)
        if not duration_str:
            duration_str = settings.default_warning_duration

        duration_seconds, expires_at = parse_duration_string(duration_str)

        warning = await self.warning_repo.create_warning(
            guild_id=guild.id,
            user_id=target.id,
            moderator_id=issuer.id,
            reason=reason,
            warning_type=warning_type,
            evidence_url=evidence_url,
            duration_seconds=duration_seconds,
            expires_at=expires_at
        )

        # Log evidence to Evidence channel if configured
        await self.send_evidence_log(guild, settings, warning, issuer, target)

        # Check Staff Demotion or Automated Punishment threshold if formal warning
        punishment_msg = None
        if warning_type == "formal" and settings.staff_demotion_enabled:
            active_count = await self.warning_repo.get_active_formal_warning_count(guild.id, target.id)
            if active_count >= settings.staff_demotion_threshold:
                punishment_msg = await self.apply_staff_demotion(guild, target, settings, active_count)

        return warning, punishment_msg

    async def send_evidence_log(
        self,
        guild: discord.Guild,
        settings: WarningSettings,
        warning: Warning,
        issuer: discord.Member,
        target: discord.Member
    ):
        if not settings.evidence_channel_id:
            return

        channel = guild.get_channel(settings.evidence_channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            return

        embed = discord.Embed(
            title=f"📋 سجل أدلة تحذير | ID: `{warning.warning_id}`",
            color=discord.Color.red() if warning.warning_type == "formal" else discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="العضو المحذر", value=f"{target.mention} (`{target.id}`)", inline=True)
        embed.add_field(name="المشرف المسؤول", value=f"{issuer.mention} (`{issuer.id}`)", inline=True)
        embed.add_field(name="نوع التحذير", value="تحذير رسمي (Formal)" if warning.warning_type == "formal" else "تحذير شفهي (Verbal)", inline=True)
        embed.add_field(name="السبب", value=warning.reason, inline=False)
        if warning.expires_at:
            embed.add_field(name="تاريخ الانتهاء", value=f"<t:{int(warning.expires_at.timestamp())}:R>", inline=True)
        else:
            embed.add_field(name="المدة", value="دائم", inline=True)

        if warning.evidence_url:
            embed.add_field(name="رابط الدليل", value=f"[اضغط هنا لرؤية الدليل]({warning.evidence_url})", inline=False)
            if warning.evidence_url.lower().endswith(('.jpg', '.png', '.jpeg', '.gif', '.webp')):
                embed.set_image(url=warning.evidence_url)

        embed.set_footer(text=f"Guild ID: {guild.id}")

        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send evidence log embed: {e}")

    async def apply_staff_demotion(
        self,
        guild: discord.Guild,
        target: discord.Member,
        settings: WarningSettings,
        active_count: int
    ) -> str:
        action = settings.demotion_action
        reason = f"تجاوز الحد الأقصى للتحذيرات الرسمية ({active_count}/{settings.staff_demotion_threshold})"

        try:
            if action == "remove_roles":
                # Remove all non-everyone roles that are manageable
                roles_to_remove = [r for r in target.roles if not r.is_default() and r.position < guild.me.top_role.position]
                if roles_to_remove:
                    await target.remove_roles(*roles_to_remove, reason=reason)
                return f"⚠️ تم تجريد العضو من جميع الرتب بسبب وصوله إلى {active_count} تحذيرات رسمية."

            elif action == "timeout":
                await target.timeout(timedelta(days=7), reason=reason)
                return f"⚠️ تم إعطاء العضو تايم أوت لمدة 7 أيام بسبب وصوله إلى {active_count} تحذيرات رسمية."

            elif action == "kick":
                await target.kick(reason=reason)
                return f"⚠️ تم طرد العضو من السيرفر بسبب وصوله إلى {active_count} تحذيرات رسمية."

        except Exception as e:
            logger.error(f"Failed to apply staff demotion action '{action}' on user {target.id}: {e}")
            return f"⚠️ تعذر تطبيق عقوبة تجريد الرتب تلقائيًا: {e}"

        return f"⚠️ وصل العضو إلى {active_count} تحذيرات رسمية."

    async def get_warnings(
        self,
        guild_id: int,
        user_id: int,
        status: Optional[str] = None,
        warning_type: Optional[str] = None
    ) -> List[Warning]:
        return await self.warning_repo.get_user_warnings(guild_id, user_id, status, warning_type)

    async def get_warning_by_id(self, guild_id: int, warning_id: str) -> Optional[Warning]:
        return await self.warning_repo.get_warning(guild_id, warning_id)

    async def edit_warning(
        self,
        guild_id: int,
        warning_id: str,
        editor_id: int,
        new_reason: Optional[str] = None,
        new_evidence: Optional[str] = None,
        new_duration_str: Optional[str] = None
    ) -> Optional[Warning]:
        expires_at = None
        if new_duration_str:
            _, expires_at = parse_duration_string(new_duration_str)

        return await self.warning_repo.edit_warning(
            guild_id=guild_id,
            warning_id=warning_id,
            editor_id=editor_id,
            new_reason=new_reason,
            new_evidence=new_evidence,
            new_expires_at=expires_at
        )

    async def remove_warning(
        self,
        guild_id: int,
        warning_id: str,
        remover_id: int,
        reason: str,
        void: bool = False
    ) -> Optional[Warning]:
        status = "VOIDED" if void else "REMOVED"
        return await self.warning_repo.remove_warning(
            guild_id=guild_id,
            warning_id=warning_id,
            remover_id=remover_id,
            removal_reason=reason,
            status=status
        )

    async def force_expire_warning(self, guild_id: int, warning_id: str) -> Optional[Warning]:
        return await self.warning_repo.expire_warning(guild_id, warning_id)
