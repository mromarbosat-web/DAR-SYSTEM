import logging
from typing import Optional, List, Tuple
import discord
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.repositories.moderation_repository import ModerationRepository
from bot.services.log_service import LogService
from bot.utils.audit_logs import format_id
from bot.utils.permissions import check_hierarchy
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.moderation_service")

class ModerationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mod_repo = ModerationRepository(session)
        self.log_service = LogService(session)

    async def warn_user(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        target: discord.Member,
        reason: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Warns a member, records warning ID, checks punishment ladder, logs event.
        Returns (success: bool, message: str, escalated_action: Optional[str])
        """
        # 1. Hierarchy Check
        can_act, h_reason = check_hierarchy(moderator, target)
        if not can_act:
            return False, h_reason, None

        # 2. Add Warning to Database
        warning = await self.mod_repo.add_warning(
            guild_id=guild.id,
            user_id=target.id,
            moderator_id=moderator.id,
            reason=reason
        )

        # 3. Log Action in Database
        await self.mod_repo.log_moderation_action(
            guild_id=guild.id,
            user_id=target.id,
            moderator_id=moderator.id,
            action_type="warn",
            reason=reason
        )

        # 4. Count total warnings for ladder trigger
        warn_count = await self.mod_repo.get_user_warning_count(guild.id, target.id)
        punish_settings = await self.mod_repo.get_punishment_settings(guild.id)

        escalated_action = None
        if warn_count == 3 and punish_settings.warn_3_action != "none":
            escalated_action = punish_settings.warn_3_action
        elif warn_count == 5 and punish_settings.warn_5_action != "none":
            escalated_action = punish_settings.warn_5_action
        elif warn_count >= 7 and punish_settings.warn_7_action != "none":
            escalated_action = punish_settings.warn_7_action

        # Apply Escalated Punishment if triggered
        ladder_note = ""
        if escalated_action:
            if "timeout" in escalated_action:
                try:
                    await target.timeout(
                        discord.utils.utcnow() + discord.utils.timedelta(hours=1),
                        reason=f"تجاوز عدد التحذيرات ({warn_count} تحذيرات)"
                    )
                    ladder_note = " (تم تطبيق عزل مؤقت تلقائي - Timeout)"
                except Exception as e:
                    logger.error(f"Failed ladder timeout: {e}")
            elif escalated_action == "kick":
                try:
                    await target.kick(reason=f"تجاوز عدد التحذيرات ({warn_count} تحذيرات)")
                    ladder_note = " (تم طرد العضو تلقائيًا - Kick)"
                except Exception as e:
                    logger.error(f"Failed ladder kick: {e}")
            elif escalated_action == "ban":
                try:
                    await target.ban(reason=f"تجاوز عدد التحذيرات ({warn_count} تحذيرات)")
                    ladder_note = " (تم حظر العضو تلقائيًا - Ban)"
                except Exception as e:
                    logger.error(f"Failed ladder ban: {e}")

        # Send DM to warned user
        try:
            dm_embed = EmbedBuilder.warning(
                title=f"تلقيت تحذيرًا في سيرفر {guild.name}",
                description=f"**السبب:** {reason}\n**معرف التحذير:** `{warning.warning_id}`\n**إجمالي التحذيرات:** `{warn_count}`"
            )
            await target.send(embed=dm_embed)
        except Exception:
            pass # Ignore if DMs are closed

        # Log Moderation Event
        fields = [
            ("👤 المستهدف", target.mention, True),
            ("🆔 المعرف", format_id(target.id), True),
            ("👮 المشرف", moderator.mention, True),
            ("📄 رقم التحذير", f"`{warning.warning_id}`", True),
            ("📊 إجمالي التحذيرات", f"`{warn_count}`", True),
            ("📝 السبب", f"`{reason}`", False)
        ]
        if ladder_note:
            fields.append(("🛡️ عقوبة إضافية", f"`{ladder_note.strip()}`", False))

        embed = EmbedBuilder.log(
            title="⚠️ توجيه تحذير (Warning)",
            color=discord.Color.gold(),
            fields=fields,
            author=moderator
        )
        await self.log_service.log_event(guild, "moderation", embed)

        msg = f"تم تحذير العضو {target.mention} بنجاح. رقم التحذير: `{warning.warning_id}` (إجمالي التحذيرات: `{warn_count}`){ladder_note}"
        return True, msg, escalated_action
