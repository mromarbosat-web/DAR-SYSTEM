import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from bot.database.connection import AsyncSessionLocal
from bot.services.voice_service import VoiceService
from bot.utils.hierarchy import has_voice_permission
from bot.utils.logger import logger

class VoiceCog(commands.Cog):
    """نظام التحكم والترتيب المتقدم للقنوات الصوتية"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    voice_group = app_commands.Group(name="voice", description="أوامر إدارة وإصدار إجراءات القنوات الصوتية")

    @voice_group.command(name="move", description="نقل عضو أو جميع أعضاء قناة صوتية إلى قناة أخرى")
    @app_commands.describe(
        target_channel="القناة الصوتية المستهدفة للنقل إليها",
        member="العضو المراد نقله بمفرده (اختياري)",
        source_channel="القناة الصوتية المراد نقل جميع أعضائها (اختياري)"
    )
    async def move_command(
        self,
        interaction: discord.Interaction,
        target_channel: discord.VoiceChannel,
        member: Optional[discord.Member] = None,
        source_channel: Optional[discord.VoiceChannel] = None
    ):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = VoiceService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not has_voice_permission(interaction.user, "move", settings):
                await interaction.followup.send("❌ لا تملك صلاحية نقل الأعضاء في القنوات الصوتية.", ephemeral=True)
                return

            if not member and not source_channel:
                if interaction.user.voice and interaction.user.voice.channel:
                    source_channel = interaction.user.voice.channel
                else:
                    await interaction.followup.send("❌ يرجى تحديد عضو أو قناة صوتية مصدر للنقل منها.", ephemeral=True)
                    return

            moved, errors = await service.move_members(
                guild=interaction.guild,
                executor=interaction.user,
                target_channel=target_channel,
                member=member,
                source_channel=source_channel
            )

            msg = f"✅ تم نقل {moved} عضو إلى {target_channel.mention} بنجاح."
            if errors:
                msg += "\n\n⚠️ **تنبيهات/أخطاء:**\n" + "\n".join(errors[:5])

            await interaction.followup.send(msg)

    @voice_group.command(name="disconnect", description="فصل عضو أو جميع أعضاء قناة صوتية")
    @app_commands.describe(
        member="العضو المراد فصله (اختياري)",
        channel="القناة الصوتية المراد فصل جميع أعضائها (اختياري)"
    )
    async def disconnect_command(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
        channel: Optional[discord.VoiceChannel] = None
    ):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = VoiceService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not has_voice_permission(interaction.user, "disconnect", settings):
                await interaction.followup.send("❌ لا تملك صلاحية فصل الأعضاء من القنوات الصوتية.", ephemeral=True)
                return

            if not member and not channel:
                if interaction.user.voice and interaction.user.voice.channel:
                    channel = interaction.user.voice.channel
                else:
                    await interaction.followup.send("❌ يرجى تحديد عضو أو قناة صوتية لفصل الأعضاء منها.", ephemeral=True)
                    return

            count, errors = await service.disconnect_members(
                guild=interaction.guild,
                executor=interaction.user,
                member=member,
                channel=channel
            )

            msg = f"✅ تم فصل {count} عضو من القناة الصوتية."
            if errors:
                msg += "\n\n⚠️ **تنبيهات/أخطاء:**\n" + "\n".join(errors[:5])

            await interaction.followup.send(msg)

    @voice_group.command(name="mute", description="كتم صوت عضو أو جميع أعضاء القناة الصوتية (Server Mute)")
    @app_commands.describe(
        member="العضو المراد كتمه (اختياري)",
        channel="القناة الصوتية المراد كتم جميع أعضائها (اختياري)",
        reason="سبب الكتم"
    )
    async def mute_command(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
        channel: Optional[discord.VoiceChannel] = None,
        reason: Optional[str] = "كتم صوتي بواسطة المشرف"
    ):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = VoiceService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not has_voice_permission(interaction.user, "mute", settings):
                await interaction.followup.send("❌ لا تملك صلاحية كتم الأعضاء صوتیًا.", ephemeral=True)
                return

            if not member and not channel:
                if interaction.user.voice and interaction.user.voice.channel:
                    channel = interaction.user.voice.channel
                else:
                    await interaction.followup.send("❌ يرجى تحديد عضو أو قناة صوتية.", ephemeral=True)
                    return

            count, errors = await service.set_mute_state(
                guild=interaction.guild,
                executor=interaction.user,
                mute=True,
                member=member,
                channel=channel,
                reason=reason
            )

            msg = f"🔇 تم كتم {count} عضو صوتیًا بنجاح."
            if errors:
                msg += "\n\n⚠️ **تنبيهات/أخطاء:**\n" + "\n".join(errors[:5])

            await interaction.followup.send(msg)

    @voice_group.command(name="unmute", description="إلغاء كتم صوت عضو أو جميع أعضاء القناة الصوتية")
    @app_commands.describe(
        member="العضو المراد إلغاء كتمه (اختياري)",
        channel="القناة الصوتية المراد إلغاء كتم جميع أعضائها (اختياري)",
        reason="السبب"
    )
    async def unmute_command(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
        channel: Optional[discord.VoiceChannel] = None,
        reason: Optional[str] = "إلغاء كتم صوتي"
    ):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = VoiceService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not has_voice_permission(interaction.user, "unmute", settings):
                await interaction.followup.send("❌ لا تملك صلاحية إلغاء كتم الأعضاء صوتيًا.", ephemeral=True)
                return

            if not member and not channel:
                if interaction.user.voice and interaction.user.voice.channel:
                    channel = interaction.user.voice.channel
                else:
                    await interaction.followup.send("❌ يرجى تحديد عضو أو قناة صوتية.", ephemeral=True)
                    return

            count, errors = await service.set_mute_state(
                guild=interaction.guild,
                executor=interaction.user,
                mute=False,
                member=member,
                channel=channel,
                reason=reason
            )

            msg = f"🔊 تم إلغاء كتم {count} عضو صوتياً بنجاح."
            if errors:
                msg += "\n\n⚠️ **تنبيهات/أخطاء:**\n" + "\n".join(errors[:5])

            await interaction.followup.send(msg)

    @voice_group.command(name="lock", description="قفل القناة الصوتية ومنع الدخول إليها")
    @app_commands.describe(
        channel="القناة الصوتية المراد قفلها (اختياري، الافتراضي قناتك الحالية)",
        user_limit="تحديد الحد الأقصى للمستخدمين القائمين (اختياري)",
        reason="سبب القفل"
    )
    async def lock_command(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.VoiceChannel] = None,
        user_limit: Optional[int] = None,
        reason: Optional[str] = "قفل قناة صوتية"
    ):
        await interaction.response.defer(ephemeral=False)
        target_channel = channel or (interaction.user.voice.channel if interaction.user.voice else None)

        if not target_channel:
            await interaction.followup.send("❌ يرجى تحديد قناة صوتية أو التواجد في إحداها أولاً.", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            service = VoiceService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not has_voice_permission(interaction.user, "lock", settings):
                await interaction.followup.send("❌ لا تملك صلاحية قفل القنوات الصوتية.", ephemeral=True)
                return

            success = await service.lock_channel(
                guild=interaction.guild,
                executor=interaction.user,
                channel=target_channel,
                user_limit=user_limit,
                reason=reason
            )

            if success:
                await interaction.followup.send(f"🔒 تم قفل القناة الصوتية {target_channel.mention} بنجاح.")
            else:
                await interaction.followup.send(f"❌ فشل قفل القناة الصوتية {target_channel.mention}.")

    @voice_group.command(name="unlock", description="فتح القناة الصوتية المقفلة")
    @app_commands.describe(
        channel="القناة الصوتية المراد فتحها (اختياري، الافتراضي قناتك الحالية)",
        reason="سبب الفتح"
    )
    async def unlock_command(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.VoiceChannel] = None,
        reason: Optional[str] = "فتح قناة صوتية"
    ):
        await interaction.response.defer(ephemeral=False)
        target_channel = channel or (interaction.user.voice.channel if interaction.user.voice else None)

        if not target_channel:
            await interaction.followup.send("❌ يرجى تحديد قناة صوتية أو التواجد في إحداها أولاً.", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            service = VoiceService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not has_voice_permission(interaction.user, "unlock", settings):
                await interaction.followup.send("❌ لا تملك صلاحية فتح القنوات الصوتية.", ephemeral=True)
                return

            success = await service.unlock_channel(
                guild=interaction.guild,
                executor=interaction.user,
                channel=target_channel,
                reason=reason
            )

            if success:
                await interaction.followup.send(f"🔓 تم فتح القناة الصوتية {target_channel.mention} بنجاح.")
            else:
                await interaction.followup.send(f"❌ فشل فتح القناة الصوتية {target_channel.mention}.")

    @voice_group.command(name="settings", description="ضبط إعدادات ورتب تسجيل القنوات الصوتية")
    @app_commands.describe(
        manager_role="رتبة مدير القنوات الصوتية",
        log_channel="روم سجلات الأحداث الصوتية"
    )
    async def settings_command(
        self,
        interaction: discord.Interaction,
        manager_role: Optional[discord.Role] = None,
        log_channel: Optional[discord.TextChannel] = None
    ):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = VoiceService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not has_voice_permission(interaction.user, "settings", settings):
                await interaction.followup.send("❌ لا تملك صلاحية تعديل إعدادات الصوت.", ephemeral=True)
                return

            updates = {}
            if manager_role: updates["voice_manager_role_id"] = manager_role.id
            if log_channel: updates["voice_log_channel_id"] = log_channel.id

            if not updates:
                embed = discord.Embed(
                    title="🔊 إعدادات التحكم الصوتي الحالية",
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="رتبة الإدارة الصوتية", value=f"<@&{settings.voice_manager_role_id}>" if settings.voice_manager_role_id else "غير محددة (تستخدم صلاحيات Discord)", inline=True)
                embed.add_field(name="قناة السجلات الصوتية", value=f"<#{settings.voice_log_channel_id}>" if settings.voice_log_channel_id else "غير محددة (تستخدم سجل المود)", inline=True)
                await interaction.followup.send(embed=embed)
                return

            await service.update_settings(interaction.guild_id, **updates)
            await interaction.followup.send("✅ تم تحديث إعدادات التحكم بالصوت بنجاح.")

async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceCog(bot))
