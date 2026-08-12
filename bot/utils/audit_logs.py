import discord
import asyncio
from datetime import timedelta
from bot.utils.time import utc_now

async def get_audit_log_executor(guild: discord.Guild, action: discord.AuditLogAction, target_id: int = None, delay: int = 1):
    """
    Tries to find the executor of a certain action from audit logs.
    """
    if delay:
        await asyncio.sleep(delay)
    
    try:
        async for entry in guild.audit_logs(limit=5, action=action):
            # Check if entry is recent (within last 10 seconds)
            if (utc_now() - entry.created_at) < timedelta(seconds=10):
                if target_id:
                    if entry.target and entry.target.id == target_id:
                        return entry.user
                else:
                    return entry.user
    except Exception:
        pass
    return None

def format_id(item_id: int):
    return f"`{item_id}`" if item_id else "غير متاح"

def format_mention(item):
    if not item:
        return "غير متاح"
    if isinstance(item, (discord.Member, discord.User, discord.Role, discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel)):
        return item.mention
    return "غير متاح"
