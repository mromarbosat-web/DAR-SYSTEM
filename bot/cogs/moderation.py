import re
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from bot.database.connection import AsyncSessionLocal
from bot.services.moderation_service import ModerationService
from bot.services.permission_service import PermissionService
from bot.database.repositories.moderation_repository import ModerationRepository
from bot.services.log_service import LogService
from bot.utils.audit_logs import format_id, format_mention
from bot.utils.permissions import check_hierarchy
from bot.utils.embeds import EmbedBuilder

def parse_duration(duration_str: str) -> Optional[int]:
    """Parses duration string like 10m, 1h, 1d into seconds"""
    match = re.match(r"^(\d+)([s|m|h|d])$", duration_str.lower().strip())
    if not match:
        return None
    val, unit = int(match.group(1)), match.group(2)
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return val * multipliers[unit]

class ModerationCog(commands.Cog):
    """Cog providing full Slash Moderation Commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="unwarn", description="إزالة تحذير محدد باستخدام معرف التحذير ID")
    @app_commands.describe(warning_id="معرف التحذير (Warning ID)")
    async def unwarn_command(self, interaction: discord.Interaction, warning_id: str):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.has_manager_permission(interaction.user, "WARNING_REMOVE") and not interaction.user.guild_permissions.moderate_members:
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لاستخدام هذا الأمر!"), ephemeral=True)
                return

            repo = ModerationRepository(session)
            # Fetch warning first to get user info for logging
            from sqlalchemy import select
            from bot.database.models import Warning as WarningModel
            stmt = select(WarningModel).where(WarningModel.guild_id == interaction.guild.id, WarningModel.warning_id == warning_id.strip())
            warning_obj = (await session.execute(stmt)).scalar_one_or_none()
            
            removed = await repo.remove_warning(interaction.guild.id, warning_id.strip())

            if removed:
                if warning_obj:
                    fields = [
                        ("👤 المستهدف", f"<@{warning_obj.user_id}>", True),
                        ("🆔 المعرف", format_id(warning_obj.user_id), True),
                        ("👮 المشرف", interaction.user.mention, True),
                        ("📄 رقم التحذير", f"`{warning_id}`", True)
                    ]
                    log_embed = EmbedBuilder.log(
                        title="🗑️ إزالة تحذير (Unwarn)",
                        color=discord.Color.green(),
                        fields=fields,
                        author=interaction.user
                    )
                    log_svc = LogService(session)
                    await log_svc.log_event(interaction.guild, "moderation", log_embed)
                
                embed = EmbedBuilder.success("تم إزالة التحذير", f"تم إزالة التحذير رقم `{warning_id}` بنجاح.")
            else:
                embed = EmbedBuilder.error("لم يتم العثور على التحذير", f"لم يتم العثور على تحذير مطابق للـ ID `{warning_id}`.")

            await interaction.followup.send(embed=embed)

    @app_commands.command(name="timeout", description="إخضاع عضو لعزل مؤقت (Timeout)")
    @app_commands.describe(user="العضو المستهدف", duration="المدة (مثال: 10m, 1h, 1d)", reason="سبب العزل")
    async def timeout_command(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str = "No reason provided"):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.has_manager_permission(interaction.user, "MOD_TIMEOUT") and not interaction.user.guild_permissions.moderate_members:
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لاستخدام هذا الأمر!"), ephemeral=True)
                return

        can_act, h_reason = check_hierarchy(interaction.user, user)
        if not can_act:
            await interaction.followup.send(embed=EmbedBuilder.error("تعذر التنفيذ", h_reason))
            return

        seconds = parse_duration(duration)
        if not seconds or seconds > 2419200: # Max 28 days
            await interaction.followup.send(embed=EmbedBuilder.error("صيغة مدة غير صحيحة", "يرجى كتابة المدة بشكل صحيح مثل: `10m` أو `1h` أو `1d` (الحد الأقصى 28 يوم)."))
            return

        try:
            until_dt = discord.utils.utcnow() + discord.utils.timedelta(seconds=seconds)
            
            # Send DM first
            dm_embed = EmbedBuilder.error(
                title="⚠️ تم تطبيق عزل مؤقت بحقك",
                description=f"تم تطبيق عزل مؤقت (Timeout) عليك في سيرفر **{interaction.guild.name}**.\n\n"
                            f"**المدة:** `{duration}`\n"
                            f"**السبب:** `{reason}`\n\n"
                            f"💡 يرجى الالتزام بالقوانين لتجنب العقوبات الأشد في المرات القادمة."
            )
            try: await user.send(embed=dm_embed)
            except: pass

            await user.timeout(until_dt, reason=reason)

            async with AsyncSessionLocal() as session:
                repo = ModerationRepository(session)
                log_svc = LogService(session)

                await repo.log_moderation_action(
                    guild_id=interaction.guild.id,
                    user_id=user.id,
                    moderator_id=interaction.user.id,
                    action_type="timeout",
                    reason=reason,
                    duration=seconds
                )

                fields = [
                    ("👤 المستهدف", user.mention, True),
                    ("🆔 المعرف", format_id(user.id), True),
                    ("👮 المشرف", interaction.user.mention, True),
                    ("⏰ المدة", f"`{duration}`", True),
                    ("📝 السبب", f"`{reason}`", False)
                ]
                log_embed = EmbedBuilder.log(
                    title="⏳ عزل مؤقت (Timeout)",
                    color=discord.Color.orange(),
                    fields=fields,
                    author=interaction.user
                )
                await log_svc.log_event(interaction.guild, "moderation", log_embed)

            await interaction.followup.send(embed=EmbedBuilder.success("تم تطبيق العزل المؤقت", f"تم عزل العضو {user.mention} لمدة `{duration}`.\n**السبب:** {reason}"))

        except discord.Forbidden:
            await interaction.followup.send(embed=EmbedBuilder.error("صلاحيات غير كافية", "لا يمتلك البوت صلاحية كافية لتطبيق Timeout على هذا العضو."))

    @app_commands.command(name="untimeout", description="إلغاء العزل المؤقت عن عضو")
    @app_commands.describe(user="العضو المراد فك عزله", reason="السبب")
    async def untimeout_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Untimeout by Moderator"):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.has_manager_permission(interaction.user, "MOD_TIMEOUT") and not interaction.user.guild_permissions.moderate_members:
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لاستخدام هذا الأمر!"), ephemeral=True)
                return

        try:
            await user.timeout(None, reason=reason)
            
            async with AsyncSessionLocal() as session:
                log_svc = LogService(session)
                fields = [
                    ("👤 المستهدف", user.mention, True),
                    ("🆔 المعرف", format_id(user.id), True),
                    ("👮 المشرف", interaction.user.mention, True),
                    ("📝 السبب", f"`{reason}`", False)
                ]
                log_embed = EmbedBuilder.log(
                    title="🔊 فك العزل المؤقت (Untimeout)",
                    color=discord.Color.green(),
                    fields=fields,
                    author=interaction.user
                )
                await log_svc.log_event(interaction.guild, "moderation", log_embed)

            await interaction.followup.send(embed=EmbedBuilder.success("تم فك العزل المؤقت", f"تم فك العزل المؤقت عن {user.mention} بنجاح."))
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("تعذر التنفيذ", f"حدث خطأ أثناء فك العزل: {e}"))

    @app_commands.command(name="kick", description="طرد عضو من السيرفر")
    @app_commands.describe(user="العضو المرادطرده", reason="سبب الطرد")
    async def kick_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.has_manager_permission(interaction.user, "MOD_KICK") and not interaction.user.guild_permissions.kick_members:
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لاستخدام هذا الأمر!"), ephemeral=True)
                return

        can_act, h_reason = check_hierarchy(interaction.user, user)
        if not can_act:
            await interaction.followup.send(embed=EmbedBuilder.error("تعذر التنفيذ", h_reason))
            return

        try:
            # Send DM first
            dm_embed = EmbedBuilder.error(
                title="👢 تم طردك من السيرفر",
                description=f"لقد تم طردك من سيرفر **{interaction.guild.name}**.\n\n"
                            f"**السبب:** `{reason}`\n\n"
                            f"💡 يمكنك العودة للسيرفر في حال حصلت على رابط دعوة جديد، ولكن يرجى الالتزام بالقوانين."
            )
            try: await user.send(embed=dm_embed)
            except: pass

            await user.kick(reason=reason)

            async with AsyncSessionLocal() as session:
                repo = ModerationRepository(session)
                log_svc = LogService(session)

                await repo.log_moderation_action(
                    guild_id=interaction.guild.id,
                    user_id=user.id,
                    moderator_id=interaction.user.id,
                    action_type="kick",
                    reason=reason
                )

                fields = [
                    ("👤 المستهدف", user.mention, True),
                    ("🆔 المعرف", format_id(user.id), True),
                    ("👮 المشرف", interaction.user.mention, True),
                    ("📝 السبب", f"`{reason}`", False)
                ]
                log_embed = EmbedBuilder.log(
                    title="👢 طرد عضو (Kick)",
                    color=discord.Color.orange(),
                    fields=fields,
                    author=interaction.user
                )
                await log_svc.log_event(interaction.guild, "moderation", log_embed)

            await interaction.followup.send(embed=EmbedBuilder.success("تم طرد العضو", f"تم طرد {user.mention} بنجاح من السيرفر.\n**السبب:** {reason}"))

        except discord.Forbidden:
            await interaction.followup.send(embed=EmbedBuilder.error("صلاحيات غير كافية", "لا يمتلك البوت صلاحية طرد هذا العضو."))

    @app_commands.command(name="ban", description="حظر عضو نهائيًا من السيرفر")
    @app_commands.describe(user="العضو المراد حظره", reason="سبب الحظر", delete_days="حذف الرسائل السابقة (0 إلى 7 أيام)")
    async def ban_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided", delete_days: int = 0):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.has_manager_permission(interaction.user, "MOD_BAN") and not interaction.user.guild_permissions.ban_members:
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لاستخدام هذا الأمر!"), ephemeral=True)
                return

        can_act, h_reason = check_hierarchy(interaction.user, user)
        if not can_act:
            await interaction.followup.send(embed=EmbedBuilder.error("تعذر التنفيذ", h_reason))
            return

        try:
            # Send DM first
            dm_embed = EmbedBuilder.error(
                title="🔨 تم حظرك من السيرفر",
                description=f"لقد تم حظرك نهائياً من سيرفر **{interaction.guild.name}**.\n\n"
                            f"**السبب:** `{reason}`\n\n"
                            f"🚫 في حال تكرار المخالفات أو محاولة الدخول بحسابات أخرى، سيتم اتخاذ إجراءات صارمة."
            )
            try: await user.send(embed=dm_embed)
            except: pass

            await user.ban(reason=reason, delete_message_days=min(max(delete_days, 0), 7))

            async with AsyncSessionLocal() as session:
                repo = ModerationRepository(session)
                log_svc = LogService(session)

                await repo.log_moderation_action(
                    guild_id=interaction.guild.id,
                    user_id=user.id,
                    moderator_id=interaction.user.id,
                    action_type="ban",
                    reason=reason
                )

                fields = [
                    ("👤 المستهدف", user.mention, True),
                    ("🆔 المعرف", format_id(user.id), True),
                    ("👮 المشرف", interaction.user.mention, True),
                    ("📝 السبب", f"`{reason}`", False)
                ]
                log_embed = EmbedBuilder.log(
                    title="🔨 حظر عضو (Ban)",
                    color=discord.Color.red(),
                    fields=fields,
                    author=interaction.user
                )
                await log_svc.log_event(interaction.guild, "moderation", log_embed)

            await interaction.followup.send(embed=EmbedBuilder.success("تم حظر العضو", f"تم حظر {user.mention} بنجاح من السيرفر.\n**السبب:** {reason}"))

        except discord.Forbidden:
            await interaction.followup.send(embed=EmbedBuilder.error("صلاحيات غير كافية", "لا يمتلك البوت صلاحية حظر هذا العضو."))

    @app_commands.command(name="unban", description="إلغاء حظر عضو باستخدام User ID")
    @app_commands.describe(user_id="معرف المستخدم (User ID)", reason="السبب")
    async def unban_command(self, interaction: discord.Interaction, user_id: str, reason: str = "Unbanned by Moderator"):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.has_manager_permission(interaction.user, "MOD_BAN") and not interaction.user.guild_permissions.ban_members:
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لاستخدام هذا الأمر!"), ephemeral=True)
                return

        try:
            uid = int(user_id.strip())
            user = await self.bot.fetch_user(uid)
            await interaction.guild.unban(user, reason=reason)
            
            async with AsyncSessionLocal() as session:
                log_svc = LogService(session)
                fields = [
                    ("👤 المستهدف", user.mention, True),
                    ("🆔 المعرف", format_id(uid), True),
                    ("👮 المشرف", interaction.user.mention, True),
                    ("📝 السبب", f"`{reason}`", False)
                ]
                log_embed = EmbedBuilder.log(
                    title="🔓 فك حظر (Unban)",
                    color=discord.Color.green(),
                    fields=fields,
                    author=interaction.user
                )
                await log_svc.log_event(interaction.guild, "moderation", log_embed)

            await interaction.followup.send(embed=EmbedBuilder.success("تم فك الحظر", f"تم إلغاء حظر المستخدم **{user}** (`{uid}`) بنجاح."))
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("تعذر إلغاء الحظر", f"حدث خطأ أثناء محاولة إلغاء الحظر: {e}"))

    @app_commands.command(name="softban", description="حظر ثم فك حظر فورًا لتطهير رسائل العضو الأخيرة")
    @app_commands.describe(user="العضو المستهدف", reason="سبب الـ Softban")
    async def softban_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Softban message purge"):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.has_manager_permission(interaction.user, "MOD_BAN") and not interaction.user.guild_permissions.ban_members:
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لاستخدام هذا الأمر!"), ephemeral=True)
                return

        can_act, h_reason = check_hierarchy(interaction.user, user)
        if not can_act:
            await interaction.followup.send(embed=EmbedBuilder.error("تعذر التنفيذ", h_reason))
            return

        try:
            await user.ban(reason=f"Softban: {reason}", delete_message_days=1)
            await interaction.guild.unban(user, reason="Softban completion")
            
            async with AsyncSessionLocal() as session:
                log_svc = LogService(session)
                fields = [
                    ("👤 المستهدف", user.mention, True),
                    ("🆔 المعرف", format_id(user.id), True),
                    ("👮 المشرف", interaction.user.mention, True),
                    ("📝 السبب", f"`{reason}`", False)
                ]
                log_embed = EmbedBuilder.log(
                    title="🌀 حظر مؤقت (Softban)",
                    color=discord.Color.blue(),
                    fields=fields,
                    author=interaction.user
                )
                await log_svc.log_event(interaction.guild, "moderation", log_embed)

            await interaction.followup.send(embed=EmbedBuilder.success("تم تنفيذ Softban", f"تم طرد العضو {user.mention} وحذف رسائله الأخيرة بنجاح (يمكنه إعادة الدخول)."))
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("فشل التنفيذ", f"حدث خطأ: {e}"))

    @app_commands.command(name="purge", description="مسح عدد محدد من الرسائل في القناة الحالية")
    @app_commands.describe(amount="عدد الرسائل المراد حذفها (1 إلى 100)", user="تصفية الحذف لعضو معين فقط (اختياري)")
    async def purge_command(self, interaction: discord.Interaction, amount: int, user: Optional[discord.Member] = None):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.has_manager_permission(interaction.user, "MOD_PURGE") and not interaction.user.guild_permissions.manage_messages:
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لاستخدام هذا الأمر!"), ephemeral=True)
                return

        if amount < 1 or amount > 100:
            await interaction.followup.send(embed=EmbedBuilder.error("خطأ بالقيمة", "يرجى تحديد عدد رسائل بين 1 و 100."), ephemeral=True)
            return

        def check(m):
            return user is None or m.author.id == user.id

        try:
            deleted = await interaction.channel.purge(limit=amount, check=check)
            
            async with AsyncSessionLocal() as session:
                log_svc = LogService(session)
                fields = [
                    ("📺 القناة", interaction.channel.mention, True),
                    ("👮 المشرف", interaction.user.mention, True),
                    ("📊 العدد المحذوف", f"`{len(deleted)}`", True)
                ]
                if user:
                    fields.append(("👤 خاص بالعضو", user.mention, True))
                    
                log_embed = EmbedBuilder.log(
                    title="🧹 مسح رسائل (Purge)",
                    color=discord.Color.dark_grey(),
                    fields=fields,
                    author=interaction.user
                )
                await log_svc.log_event(interaction.guild, "moderation", log_embed)

            msg = f"تم مسح **{len(deleted)}** رسالة بنجاح."
            if user:
                msg += f" (الخاصة بالعضو {user.mention})"
            await interaction.followup.send(embed=EmbedBuilder.success("تم مسح الرسائل", msg), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("فشل مسح الرسائل", f"حدث خطأ: {e}"), ephemeral=True)

    @app_commands.command(name="slowmode", description="ضبط الوضع البطيء (Slowmode) للقناة النصية")
    @app_commands.describe(seconds="المدة بالثواني بين كل رسالة (0 لإلغاء Slowmode)")
    async def slowmode_command(self, interaction: discord.Interaction, seconds: int):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.has_manager_permission(interaction.user, "MOD_SLOWMODE") and not interaction.user.guild_permissions.manage_channels:
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لاستخدام هذا الأمر!"), ephemeral=True)
                return

        if seconds < 0 or seconds > 21600:
            await interaction.followup.send(embed=EmbedBuilder.error("قيمة غير صحيحة", "الوضع البطيء يجب أن يكون بين 0 و 21600 ثانية (6 ساعات)."))
            return

        try:
            await interaction.channel.edit(slowmode_delay=seconds)
            
            async with AsyncSessionLocal() as session:
                log_svc = LogService(session)
                fields = [
                    ("📺 القناة", interaction.channel.mention, True),
                    ("👮 المشرف", interaction.user.mention, True),
                    ("⏰ المدة", f"`{seconds}` ثانية", True)
                ]
                log_embed = EmbedBuilder.log(
                    title="⏳ تعديل الوضع البطيء (Slowmode)",
                    color=discord.Color.dark_teal(),
                    fields=fields,
                    author=interaction.user
                )
                await log_svc.log_event(interaction.guild, "moderation", log_embed)

            if seconds == 0:
                embed = EmbedBuilder.success("تم إلغاء Slowmode", "تم تعطيل الوضع البطيء في هذه القناة.")
            else:
                embed = EmbedBuilder.info("تم ضبط Slowmode", f"تم ضبط فاصل الإرسال إلى **{seconds}** ثانية بين كل رسالة.")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("فشل التعديل", f"حدث خطأ: {e}"))

    @app_commands.command(name="lock", description="قفل القناة النصية الحالية ومنع الأعضاء من الكتابة")
    @app_commands.describe(reason="سبب القفل")
    async def lock_text_command(self, interaction: discord.Interaction, reason: str = "Locked by Moderator"):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.has_manager_permission(interaction.user, "MOD_LOCK_UNLOCK") and not interaction.user.guild_permissions.manage_channels:
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لاستخدام هذا الأمر!"), ephemeral=True)
                return

        try:
            overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = False
            await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason=reason)
            
            async with AsyncSessionLocal() as session:
                log_svc = LogService(session)
                await log_svc.log_event(interaction.guild, "moderation", EmbedBuilder.log(
                    title="🔒 قفل قناة نصية",
                    color=discord.Color.red(),
                    fields=[
                        ("📺 القناة", interaction.channel.mention, True),
                        ("👮 المشرف", interaction.user.mention, True),
                        ("📝 السبب", reason, False)
                    ],
                    author=interaction.user
                ))

            await interaction.followup.send(embed=EmbedBuilder.success("تم قفل القناة", "تم منع رتبة الجميع من إرسال الرسائل في هذه القناة."))
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("فشل التنفيذ", f"حدث خطأ: {e}"))

    @app_commands.command(name="unlock", description="فتح القناة النصية الحالية")
    @app_commands.describe(reason="سبب الفتح")
    async def unlock_text_command(self, interaction: discord.Interaction, reason: str = "Unlocked by Moderator"):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            perm_service = PermissionService(session)
            if not await perm_service.has_manager_permission(interaction.user, "MOD_LOCK_UNLOCK") and not interaction.user.guild_permissions.manage_channels:
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "لا تملك الصلاحية الكافية لاستخدام هذا الأمر!"), ephemeral=True)
                return

        try:
            overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = None
            await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason=reason)
            
            async with AsyncSessionLocal() as session:
                log_svc = LogService(session)
                await log_svc.log_event(interaction.guild, "moderation", EmbedBuilder.log(
                    title="🔓 فتح قناة نصية",
                    color=discord.Color.green(),
                    fields=[
                        ("📺 القناة", interaction.channel.mention, True),
                        ("👮 المشرف", interaction.user.mention, True),
                        ("📝 السبب", reason, False)
                    ],
                    author=interaction.user
                ))

            await interaction.followup.send(embed=EmbedBuilder.success("تم فتح القناة", "تمت إعادة إعدادات إرسال الرسائل لوضعها الطبيعي."))
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("فشل التنفيذ", f"حدث خطأ: {e}"))

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
