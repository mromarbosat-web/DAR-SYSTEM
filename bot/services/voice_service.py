import discord
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.repositories.voice_repository import VoiceRepository
from bot.database.repositories.log_repository import LogRepository
from bot.database.models import VoiceSettings
from bot.utils.hierarchy import can_moderate_member
from bot.utils.logger import logger

class VoiceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.voice_repo = VoiceRepository(session)
        self.log_repo = LogRepository(session)

    async def get_settings(self, guild_id: int) -> VoiceSettings:
        return await self.voice_repo.get_or_create_voice_settings(guild_id)

    async def update_settings(self, guild_id: int, **kwargs) -> VoiceSettings:
        return await self.voice_repo.update_voice_settings(guild_id, **kwargs)

    async def log_voice_event(
        self,
        guild: discord.Guild,
        executor: discord.Member,
        action_type: str,
        title: str,
        description: str,
        target: Optional[discord.Member] = None,
        channel: Optional[discord.VoiceChannel] = None
    ):
        settings = await self.get_settings(guild.id)
        log_channel_id = settings.voice_log_channel_id

        if not log_channel_id:
            # Fallback to moderation log channel
            log_settings = await self.log_repo.get_log_settings(guild.id)
            log_channel_id = log_settings.moderation_log_channel_id

        if not log_channel_id:
            return

        channel_obj = guild.get_channel(log_channel_id)
        if not channel_obj or not isinstance(channel_obj, discord.TextChannel):
            return

        embed = discord.Embed(
            title=f"🔊 إجراء صوتي: {title}",
            description=description,
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="المشرف المنفذ", value=f"{executor.mention} (`{executor.id}`)", inline=True)
        if target:
            embed.add_field(name="العضو المستهدف", value=f"{target.mention} (`{target.id}`)", inline=True)
        if channel:
            embed.add_field(name="القناة الصوتية", value=f"{channel.name} (`{channel.id}`)", inline=True)

        embed.set_footer(text=f"Guild ID: {guild.id}")

        try:
            await channel_obj.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to log voice action to channel: {e}")

    async def move_members(
        self,
        guild: discord.Guild,
        executor: discord.Member,
        target_channel: discord.VoiceChannel,
        member: Optional[discord.Member] = None,
        source_channel: Optional[discord.VoiceChannel] = None,
        reason: str = "Voice Move Command"
    ) -> Tuple[int, List[str]]:
        """
        Moves member or all members in source_channel to target_channel.
        Returns (moved_count, errors)
        """
        moved_count = 0
        errors = []

        if member:
            if not member.voice or not member.voice.channel:
                return 0, [f"العضو {member.mention} ليس متواجدًا في أي قناة صوتية."]

            allowed, hierarchy_msg = can_moderate_member(executor, member, guild.me)
            if not allowed:
                return 0, [hierarchy_msg]

            try:
                await member.move_to(target_channel, reason=reason)
                moved_count += 1
                await self.voice_repo.log_voice_action(
                    guild_id=guild.id,
                    executor_id=executor.id,
                    target_id=member.id,
                    action_type="move",
                    channel_id=member.voice.channel.id if member.voice else None,
                    target_channel_id=target_channel.id,
                    reason=reason
                )
            except Exception as e:
                errors.append(f"فشل نقل {member.mention}: {e}")

        elif source_channel:
            members_to_move = list(source_channel.members)
            for m in members_to_move:
                allowed, _ = can_moderate_member(executor, m, guild.me)
                if not allowed:
                    errors.append(f"تم تخطي {m.mention} بسبب الرتب والمستويات.")
                    continue
                try:
                    await m.move_to(target_channel, reason=reason)
                    moved_count += 1
                except Exception as e:
                    errors.append(f"فشل نقل {m.mention}: {e}")

            if moved_count > 0:
                await self.voice_repo.log_voice_action(
                    guild_id=guild.id,
                    executor_id=executor.id,
                    action_type="move_all",
                    channel_id=source_channel.id,
                    target_channel_id=target_channel.id,
                    reason=reason
                )

        if moved_count > 0:
            await self.log_voice_event(
                guild, executor, "move",
                "نقل أعضاء",
                f"تم نقل {moved_count} عضو إلى {target_channel.mention}",
                target=member, channel=target_channel
            )

        return moved_count, errors

    async def disconnect_members(
        self,
        guild: discord.Guild,
        executor: discord.Member,
        member: Optional[discord.Member] = None,
        channel: Optional[discord.VoiceChannel] = None,
        reason: str = "Voice Disconnect Command"
    ) -> Tuple[int, List[str]]:
        disconnected_count = 0
        errors = []

        if member:
            if not member.voice or not member.voice.channel:
                return 0, [f"العضو {member.mention} ليس متواجدًا في أي قناة صوتية."]

            allowed, hierarchy_msg = can_moderate_member(executor, member, guild.me)
            if not allowed:
                return 0, [hierarchy_msg]

            try:
                await member.move_to(None, reason=reason)
                disconnected_count += 1
                await self.voice_repo.log_voice_action(
                    guild_id=guild.id,
                    executor_id=executor.id,
                    target_id=member.id,
                    action_type="disconnect",
                    reason=reason
                )
            except Exception as e:
                errors.append(f"فشل فصل {member.mention}: {e}")

        elif channel:
            members = list(channel.members)
            for m in members:
                allowed, _ = can_moderate_member(executor, m, guild.me)
                if not allowed:
                    errors.append(f"تم تخطي {m.mention} بسبب الرتب والمستويات.")
                    continue
                try:
                    await m.move_to(None, reason=reason)
                    disconnected_count += 1
                except Exception as e:
                    errors.append(f"فشل فصل {m.mention}: {e}")

            if disconnected_count > 0:
                await self.voice_repo.log_voice_action(
                    guild_id=guild.id,
                    executor_id=executor.id,
                    action_type="disconnect_all",
                    channel_id=channel.id,
                    reason=reason
                )

        if disconnected_count > 0:
            await self.log_voice_event(
                guild, executor, "disconnect",
                "فصل أعضاء من القناة",
                f"تم فصل {disconnected_count} عضو من القناة الصوتية.",
                target=member, channel=channel
            )

        return disconnected_count, errors

    async def set_mute_state(
        self,
        guild: discord.Guild,
        executor: discord.Member,
        mute: bool,
        member: Optional[discord.Member] = None,
        channel: Optional[discord.VoiceChannel] = None,
        reason: str = "Voice Mute Command"
    ) -> Tuple[int, List[str]]:
        action_name = "كتم" if mute else "إلغاء كتم"
        updated_count = 0
        errors = []

        if member:
            if not member.voice or not member.voice.channel:
                return 0, [f"العضو {member.mention} ليس متواجدًا في أي قناة صوتية."]

            allowed, hierarchy_msg = can_moderate_member(executor, member, guild.me)
            if not allowed:
                return 0, [hierarchy_msg]

            try:
                await member.edit(mute=mute, reason=reason)
                updated_count += 1
                await self.voice_repo.log_voice_action(
                    guild_id=guild.id,
                    executor_id=executor.id,
                    target_id=member.id,
                    action_type="mute" if mute else "unmute",
                    channel_id=member.voice.channel.id,
                    reason=reason
                )
            except Exception as e:
                errors.append(f"فشل {action_name} {member.mention}: {e}")

        elif channel:
            members = list(channel.members)
            for m in members:
                allowed, _ = can_moderate_member(executor, m, guild.me)
                if not allowed:
                    errors.append(f"تم تخطي {m.mention} بسبب الرتب والمستويات.")
                    continue
                try:
                    await m.edit(mute=mute, reason=reason)
                    updated_count += 1
                except Exception as e:
                    errors.append(f"فشل {action_name} {m.mention}: {e}")

            if updated_count > 0:
                await self.voice_repo.log_voice_action(
                    guild_id=guild.id,
                    executor_id=executor.id,
                    action_type="mute_all" if mute else "unmute_all",
                    channel_id=channel.id,
                    reason=reason
                )

        if updated_count > 0:
            await self.log_voice_event(
                guild, executor, "mute" if mute else "unmute",
                f"{action_name} أعضاء القناة",
                f"تم {action_name} {updated_count} عضو في القناة الصوتية.",
                target=member, channel=channel
            )

        return updated_count, errors

    async def lock_channel(
        self,
        guild: discord.Guild,
        executor: discord.Member,
        channel: discord.VoiceChannel,
        user_limit: Optional[int] = None,
        reason: str = "Voice Lock Command"
    ) -> bool:
        """
        Locks voice channel by setting user_limit or denying connect to @everyone.
        """
        try:
            if user_limit is not None:
                await channel.edit(user_limit=user_limit, reason=reason)
            else:
                # Lock by denying connect to @everyone
                overwrite = channel.overwrites_for(guild.default_role)
                overwrite.connect = False
                await channel.set_permissions(guild.default_role, overwrite=overwrite, reason=reason)

            await self.voice_repo.log_voice_action(
                guild_id=guild.id,
                executor_id=executor.id,
                action_type="lock",
                channel_id=channel.id,
                reason=reason
            )

            await self.log_voice_event(
                guild, executor, "lock",
                "قفل قناة صوتية",
                f"تم قفل القناة الصوتية {channel.mention}.",
                channel=channel
            )

            return True
        except Exception as e:
            logger.error(f"Failed to lock channel {channel.id}: {e}")
            return False

    async def unlock_channel(
        self,
        guild: discord.Guild,
        executor: discord.Member,
        channel: discord.VoiceChannel,
        reason: str = "Voice Unlock Command"
    ) -> bool:
        """
        Unlocks voice channel by clearing limit or setting connect to True / None for @everyone.
        """
        try:
            await channel.edit(user_limit=0, reason=reason)
            overwrite = channel.overwrites_for(guild.default_role)
            overwrite.connect = None
            await channel.set_permissions(guild.default_role, overwrite=overwrite, reason=reason)

            await self.voice_repo.log_voice_action(
                guild_id=guild.id,
                executor_id=executor.id,
                action_type="unlock",
                channel_id=channel.id,
                reason=reason
            )

            await self.log_voice_event(
                guild, executor, "unlock",
                "فتح قناة صوتية",
                f"تم فتح القناة الصوتية {channel.mention}.",
                channel=channel
            )

            return True
        except Exception as e:
            logger.error(f"Failed to unlock channel {channel.id}: {e}")
            return False
