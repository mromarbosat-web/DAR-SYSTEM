import logging
import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.security_service import SecurityService

logger = logging.getLogger("discord_bot.events.audit_log")

def register_audit_log_event(bot: commands.Bot):
    @bot.event
    async def on_audit_log_entry_create(entry: discord.AuditLogEntry):
        guild = entry.guild
        if not guild or not entry.user:
            return

        action_name = str(entry.action)
        
        # Check if audit entry is channel/role deletion or permission change
        if "channel_delete" in action_name or "role_delete" in action_name or "overwrite" in action_name:
            async with AsyncSessionLocal() as session:
                sec_service = SecurityService(session)
                await sec_service.handle_audit_action(guild, entry, action_name)
