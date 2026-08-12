import time
import logging
from collections import defaultdict
from typing import Dict, List, Optional
import discord
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.repositories.security_repository import SecurityRepository
from bot.database.repositories.whitelist_repository import WhitelistRepository
from bot.services.log_service import LogService
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.security_service")

# In-memory trackers for rapid events
# guild_id -> list of timestamps
raid_tracker: Dict[int, List[float]] = defaultdict(list)

# guild_id -> user_id -> list of (action_type, timestamp)
nuke_tracker: Dict[int, Dict[int, List[tuple]]] = defaultdict(lambda: defaultdict(list))

class SecurityService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.sec_repo = SecurityRepository(session)
        self.wl_repo = WhitelistRepository(session)
        self.log_service = LogService(session)

    async def handle_member_join(self, member: discord.Member):
        """Processes a new member join for Anti-Raid detection"""
        guild = member.guild
        sec = await self.sec_repo.get_security_settings(guild.id)

        if not sec or not sec.anti_raid_enabled:
            return

        # Check whitelist
        role_ids = [r.id for r in member.roles]
        if await self.wl_repo.is_whitelisted(guild.id, member.id, role_ids):
            return

        now = time.time()
        window = sec.anti_raid_time_window
        threshold = sec.anti_raid_join_threshold

        # Clean old timestamps
        joins = raid_tracker[guild.id]
        raid_tracker[guild.id] = [t for t in joins if now - t <= window]
        raid_tracker[guild.id].append(now)

        current_count = len(raid_tracker[guild.id])

        if current_count >= threshold:
            logger.warning(f"Anti-Raid triggered in guild {guild.name} ({guild.id})! Joins: {current_count} in {window}s")
            
            # Execute Anti-Raid action
            action = sec.anti_raid_action.lower()
            
            if action == "lockdown":
                await self.lockdown_guild(guild, reason="Anti-Raid Automated Trigger")
            elif action == "kick":
                try:
                    await member.kick(reason="Anti-Raid Protection Triggered")
                except Exception as e:
                    logger.error(f"Failed to kick member in anti-raid: {e}")
            elif action == "ban":
                try:
                    await member.ban(reason="Anti-Raid Protection Triggered", delete_message_days=1)
                except Exception as e:
                    logger.error(f"Failed to ban member in anti-raid: {e}")
            elif action == "timeout":
                try:
                    await member.timeout(discord.utils.utcnow() + discord.utils.timedelta(hours=1), reason="Anti-Raid Trigger")
                except Exception as e:
                    logger.error(f"Failed to timeout member in anti-raid: {e}")

            # Send Security Log Embed
            embed = EmbedBuilder.security_alert(
                title="تم اكتشاف هجوم دخول جماعي (Anti-Raid Triggered)",
                description=f"تم اكتشاف دخول **{current_count}** أعضاء خلال **{window}** ثانية.",
                fields=[
                    ("السيرفر", guild.name, True),
                    ("العضو المحفز", f"{member.mention} ({member.id})", True),
                    ("الإجراء المتخذ", action.upper(), True)
                ]
            )
            await self.log_service.log_event(guild, "security", embed)

    async def handle_audit_action(self, guild: discord.Guild, entry: discord.AuditLogEntry, action_type: str):
        """Processes audit log actions (channel/role deletes, etc.) for Anti-Nuke detection"""
        if not entry.user or entry.user.bot and entry.user.id == guild.me.id:
            return

        sec = await self.sec_repo.get_security_settings(guild.id)
        if not sec or not sec.anti_nuke_enabled:
            return

        user_id = entry.user.id
        
        # Check whitelist
        user_member = guild.get_member(user_id)
        role_ids = [r.id for r in user_member.roles] if user_member else []
        if await self.wl_repo.is_whitelisted(guild.id, user_id, role_ids):
            return

        now = time.time()
        window = sec.anti_nuke_time_window
        threshold = sec.anti_nuke_channel_threshold if "channel" in action_type else sec.anti_nuke_role_threshold

        # Track actions per user
        user_actions = nuke_tracker[guild.id][user_id]
        nuke_tracker[guild.id][user_id] = [a for a in user_actions if now - a[1] <= window]
        nuke_tracker[guild.id][user_id].append((action_type, now))

        matching_actions = [a for a in nuke_tracker[guild.id][user_id] if a[0] == action_type]

        if len(matching_actions) >= threshold:
            logger.warning(f"Anti-Nuke triggered in {guild.name} by user {entry.user} ({user_id}) for {action_type}!")
            
            action = sec.anti_nuke_action.lower()
            if user_member:
                if action == "remove_roles":
                    try:
                        # Strip all assignable roles from offender
                        dangerous_roles = [r for r in user_member.roles if r.name != "@everyone" and r < guild.me.top_role]
                        if dangerous_roles:
                            await user_member.remove_roles(*dangerous_roles, reason="Anti-Nuke Security Violation")
                    except Exception as e:
                        logger.error(f"Failed to remove roles in anti-nuke: {e}")
                elif action == "ban":
                    try:
                        await user_member.ban(reason="Anti-Nuke Triggered: Mass Administrative Action", delete_message_days=0)
                    except Exception as e:
                        logger.error(f"Failed to ban in anti-nuke: {e}")

            # Send Alert to Owner & Security Log
            embed = EmbedBuilder.security_alert(
                title="تنبيه أنتي نوك خطير (Anti-Nuke Activated)",
                description=f"المستخدم {entry.user.mention} قَام بتنفيذ نشاط إداري مشبوه مكثف (**{len(matching_actions)}** إجراءات من نوع `{action_type}`).",
                fields=[
                    ("المنفذ", f"{entry.user} ({entry.user.id})", True),
                    ("النوع", action_type, True),
                    ("الإجراء الوقائي", action, True)
                ]
            )
            await self.log_service.log_event(guild, "security", embed)

    async def lockdown_guild(self, guild: discord.Guild, reason: str = "Lockdown Activated"):
        """Locks send_messages permission on all text channels for @everyone role"""
        everyone_role = guild.default_role
        for channel in guild.text_channels:
            try:
                overwrites = channel.overwrites_for(everyone_role)
                if overwrites.send_messages is not False:
                    overwrites.send_messages = False
                    await channel.set_permissions(everyone_role, overwrite=overwrites, reason=reason)
            except Exception as e:
                logger.error(f"Failed lockdown on channel {channel.name}: {e}")

    async def unlock_guild(self, guild: discord.Guild, reason: str = "Lockdown Lifted"):
        """Restores send_messages permission on text channels for @everyone role"""
        everyone_role = guild.default_role
        for channel in guild.text_channels:
            try:
                overwrites = channel.overwrites_for(everyone_role)
                if overwrites.send_messages is False:
                    overwrites.send_messages = None
                    await channel.set_permissions(everyone_role, overwrite=overwrites, reason=reason)
            except Exception as e:
                logger.error(f"Failed unlock on channel {channel.name}: {e}")
