import logging
from typing import Optional, List
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.shortcuts import CommandShortcut
from bot.utils.time import utc_now

logger = logging.getLogger("discord_bot.shortcut_repository")

# Default shortcuts for quick setup if none exist
DEFAULT_SHORTCUTS = [
    {"trigger": "تحذير", "action": "warn"},
    {"trigger": "كتم", "action": "timeout"},
    {"trigger": "عزل", "action": "timeout"},
    {"trigger": "طرد", "action": "kick"},
    {"trigger": "حظر", "action": "ban"},
    {"trigger": "تبنيد", "action": "ban"},
    {"trigger": "مسح", "action": "purge"},
    {"trigger": "قفل", "action": "lock"},
    {"trigger": "فتح", "action": "unlock"},
    {"trigger": "صوت كتم", "action": "voice_mute"},
    {"trigger": "صوت فصل", "action": "voice_disconnect"},
    {"trigger": "صوت نقل", "action": "voice_move"},
    {"trigger": "بروفايل", "action": "profile"},
    {"trigger": "رصيد", "action": "balance"},
    {"trigger": "متجر", "action": "shop"},
    {"trigger": "يومي", "action": "daily"},
    {"trigger": "تحذيراتي", "action": "warnings"},
    {"trigger": "سجل", "action": "warnings"},
]

class ShortcutRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_shortcut(self, guild_id: int, trigger_word: str) -> Optional[CommandShortcut]:
        stmt = select(CommandShortcut).where(
            CommandShortcut.guild_id == guild_id,
            CommandShortcut.trigger_word == trigger_word.strip().lower()
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_shortcuts(self, guild_id: int) -> List[CommandShortcut]:
        stmt = select(CommandShortcut).where(CommandShortcut.guild_id == guild_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def add_or_update_shortcut(
        self,
        guild_id: int,
        trigger_word: str,
        target_action: str,
        created_by: int,
        allowed_roles: Optional[str] = None,
        allowed_users: Optional[str] = None,
        allowed_channels: Optional[str] = None,
        ignored_channels: Optional[str] = None,
        enabled: bool = True
    ) -> CommandShortcut:
        trigger_clean = trigger_word.strip().lower()
        shortcut = await self.get_shortcut(guild_id, trigger_clean)
        if not shortcut:
            shortcut = CommandShortcut(
                guild_id=guild_id,
                trigger_word=trigger_clean,
                target_action=target_action,
                created_by=created_by,
                allowed_roles=allowed_roles,
                allowed_users=allowed_users,
                allowed_channels=allowed_channels,
                ignored_channels=ignored_channels,
                enabled=enabled,
                created_at=utc_now(),
                updated_at=utc_now()
            )
            self.session.add(shortcut)
        else:
            shortcut.target_action = target_action
            shortcut.allowed_roles = allowed_roles
            shortcut.allowed_users = allowed_users
            shortcut.allowed_channels = allowed_channels
            shortcut.ignored_channels = ignored_channels
            shortcut.enabled = enabled
            shortcut.updated_at = utc_now()
        
        await self.session.commit()
        await self.session.refresh(shortcut)
        return shortcut

    async def delete_shortcut(self, guild_id: int, trigger_word: str) -> bool:
        trigger_clean = trigger_word.strip().lower()
        stmt = delete(CommandShortcut).where(
            CommandShortcut.guild_id == guild_id,
            CommandShortcut.trigger_word == trigger_clean
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount > 0

    async def seed_defaults_if_empty(self, guild_id: int, owner_id: int):
        shortcuts = await self.list_shortcuts(guild_id)
        if not shortcuts:
            for item in DEFAULT_SHORTCUTS:
                sc = CommandShortcut(
                    guild_id=guild_id,
                    trigger_word=item["trigger"],
                    target_action=item["action"],
                    created_by=owner_id,
                    enabled=True,
                    created_at=utc_now(),
                    updated_at=utc_now()
                )
                self.session.add(sc)
            try:
                await self.session.commit()
            except Exception as e:
                logger.warning(f"Error seeding shortcuts: {e}")
                await self.session.rollback()
