import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, update, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import WarningSettings, Warning, WarningEvidence
from bot.database.repositories.guild_repository import GuildRepository

class WarningRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_warning_settings(self, guild_id: int) -> WarningSettings:
        stmt = select(WarningSettings).where(WarningSettings.guild_id == guild_id)
        result = await self.session.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            guild_repo = GuildRepository(self.session)
            await guild_repo.get_or_create_guild(guild_id, f"Guild_{guild_id}")
            settings = WarningSettings(guild_id=guild_id)
            self.session.add(settings)
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()
            await self.session.refresh(settings)
        return settings

    async def update_warning_settings(self, guild_id: int, **kwargs) -> WarningSettings:
        settings = await self.get_or_create_warning_settings(guild_id)
        for key, value in kwargs.items():
            if hasattr(settings, key) and value is not None:
                setattr(settings, key, value)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            await self.session.flush()
        await self.session.refresh(settings)
        return settings

    async def create_warning(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
        warning_type: str = "formal", # "formal" or "verbal"
        evidence_url: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        expires_at: Optional[datetime] = None
    ) -> Warning:
        guild_repo = GuildRepository(self.session)
        await guild_repo.get_or_create_guild(guild_id, f"Guild_{guild_id}")

        warning = Warning(
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            warning_type=warning_type,
            status="ACTIVE",
            reason=reason,
            evidence_url=evidence_url,
            duration_seconds=duration_seconds,
            expires_at=expires_at
        )
        self.session.add(warning)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            await self.session.flush()
        await self.session.refresh(warning)

        if evidence_url:
            evidence = WarningEvidence(
                warning_id=warning.warning_id,
                uploaded_by=moderator_id,
                content_url=evidence_url,
                note="Initial warning evidence"
            )
            self.session.add(evidence)
            try:
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                await self.session.flush()

        return warning

    async def add_warning_evidence(
        self,
        warning_id: str,
        uploaded_by: int,
        content_url: str,
        note: Optional[str] = None
    ) -> WarningEvidence:
        evidence = WarningEvidence(
            warning_id=warning_id,
            uploaded_by=uploaded_by,
            content_url=content_url,
            note=note
        )
        self.session.add(evidence)
        await self.session.commit()
        await self.session.refresh(evidence)
        return evidence

    async def get_warning(self, guild_id: int, warning_id: str) -> Optional[Warning]:
        stmt = (
            select(Warning)
            .options(selectinload(Warning.evidences))
            .where(and_(Warning.guild_id == guild_id, Warning.warning_id == warning_id))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_warnings(
        self,
        guild_id: int,
        user_id: int,
        status: Optional[str] = None,
        warning_type: Optional[str] = None
    ) -> List[Warning]:
        # Auto expire any outdated active warnings first
        await self.expire_outdated_warnings(guild_id, user_id)

        filters = [Warning.guild_id == guild_id, Warning.user_id == user_id]
        if status:
            filters.append(Warning.status == status)
        if warning_type:
            filters.append(Warning.warning_type == warning_type)

        stmt = (
            select(Warning)
            .options(selectinload(Warning.evidences))
            .where(and_(*filters))
            .order_by(Warning.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_formal_warning_count(self, guild_id: int, user_id: int) -> int:
        await self.expire_outdated_warnings(guild_id, user_id)
        stmt = select(func.count(Warning.warning_id)).where(
            and_(
                Warning.guild_id == guild_id,
                Warning.user_id == user_id,
                Warning.warning_type == "formal",
                Warning.status == "ACTIVE"
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_active_verbal_warning_count(self, guild_id: int, user_id: int) -> int:
        await self.expire_outdated_warnings(guild_id, user_id)
        stmt = select(func.count(Warning.warning_id)).where(
            and_(
                Warning.guild_id == guild_id,
                Warning.user_id == user_id,
                Warning.warning_type == "verbal",
                Warning.status == "ACTIVE"
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def edit_warning(
        self,
        guild_id: int,
        warning_id: str,
        editor_id: int,
        new_reason: Optional[str] = None,
        new_evidence: Optional[str] = None,
        new_expires_at: Optional[datetime] = None
    ) -> Optional[Warning]:
        warning = await self.get_warning(guild_id, warning_id)
        if not warning:
            return None

        # Record edit history
        history = json.loads(warning.edit_history) if warning.edit_history else []
        history.append({
            "edited_by": editor_id,
            "edited_at": datetime.utcnow().isoformat(),
            "old_reason": warning.reason,
            "old_evidence": warning.evidence_url,
            "old_expires_at": warning.expires_at.isoformat() if warning.expires_at else None
        })
        warning.edit_history = json.dumps(history)
        warning.edited_by = editor_id

        if new_reason:
            warning.reason = new_reason
        if new_evidence:
            warning.evidence_url = new_evidence
            await self.add_warning_evidence(warning.warning_id, editor_id, new_evidence, "Updated via warning edit")
        if new_expires_at:
            warning.expires_at = new_expires_at

        await self.session.commit()
        await self.session.refresh(warning)
        return warning

    async def remove_warning(
        self,
        guild_id: int,
        warning_id: str,
        remover_id: int,
        removal_reason: str,
        status: str = "REMOVED" # "REMOVED" or "VOIDED"
    ) -> Optional[Warning]:
        warning = await self.get_warning(guild_id, warning_id)
        if not warning:
            return None

        warning.status = status
        warning.removed_by = remover_id
        warning.removal_reason = removal_reason
        warning.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(warning)
        return warning

    async def expire_warning(self, guild_id: int, warning_id: str) -> Optional[Warning]:
        warning = await self.get_warning(guild_id, warning_id)
        if not warning:
            return None

        warning.status = "EXPIRED"
        warning.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(warning)
        return warning

    async def expire_outdated_warnings(self, guild_id: int, user_id: Optional[int] = None) -> int:
        now = datetime.utcnow()
        filters = [
            Warning.guild_id == guild_id,
            Warning.status == "ACTIVE",
            Warning.expires_at.is_not(None),
            Warning.expires_at <= now
        ]
        if user_id:
            filters.append(Warning.user_id == user_id)

        stmt = update(Warning).where(and_(*filters)).values(
            status="EXPIRED",
            updated_at=now
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
