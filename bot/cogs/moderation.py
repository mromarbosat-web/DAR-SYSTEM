import re
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from bot.database.connection import AsyncSessionLocal
from bot.services.moderation_service import ModerationService
from bot.database.repositories.moderation_repository import ModerationRepository
from bot.services.log_service import LogService
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
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(warning_id="معرف التحذير (Warning ID)")
    async def unwarn_command(self, interaction: discord.Interaction, warning_id: str):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            repo = ModerationRepository(session)
            removed = await repo.remove_warning(interaction.guild.id, warning_id.strip())

            if removed:
                embed = EmbedBuilder.success("تم إزالة التحذير", f"تم إزالة التحذير رقم `{warning_id}` بنجاح.")
            else:
                embed = EmbedBuilder.error("لم يتم العثور على التحذير", f"لم يتم العثور على تحذير مطابق للـ ID `{warning_id}`.")

            await interaction.followup.send(embed=embed)

    @app_commands.command(name="timeout", description="إخضاع عضو لعزل مؤقت (Timeout)")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(user="العضو المستهدف", duration="المدة (مثال: 10m, 1h, 1d)", reason="سبب العزل")
    async def timeout_command(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str = "No reason provided"):
        await interaction.response.defer()

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

                log_embed = EmbedBuilder.warning(
                    title="عزل مؤقت (Timeout Action)",
                    description=f"تم تطبيق العزل المؤقت على العضو {user.mention}.",
                    fields=[
                        ("العضو", f"{user} (`{user.id}`)", True),
                        ("المشرف", f"{interaction.user.mention}", True),
                        ("المدة", duration, True),
                        ("السبب", reason, False)
                    ]
                )
                await log_svc.log_event(interaction.guild, "moderation", log_embed)

            await interaction.followup.send(embed=EmbedBuilder.success("تم تطبيق العزل المؤقت", f"تم عزل العضو {user.mention} لمدة `{duration}`.\n**السبب:** {reason}"))

        except discord.Forbidden:
            await interaction.followup.send(embed=EmbedBuilder.error("صلاحيات غير كافية", "لا يمتلك البوت صلاحية كافية لتطبيق Timeout على هذا العضو."))

    @app_commands.command(name="untimeout", description="إلغاء العزل المؤقت عن عضو")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(user="العضو المراد فك عزله", reason="السبب")
    async def untimeout_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Untimeout by Moderator"):
        await interaction.response.defer()

        try:
            await user.timeout(None, reason=reason)
            await interaction.followup.send(embed=EmbedBuilder.success("تم فك العزل المؤقت", f"تم فك العزل المؤقت عن {user.mention} بنجاح."))
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("تعذر التنفيذ", f"حدث خطأ أثناء فك العزل: {e}"))

    @app_commands.command(name="kick", description="طرد عضو من السيرفر")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.describe(user="العضو المرادطرده", reason="سبب الطرد")
    async def kick_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        await interaction.response.defer()

        can_act, h_reason = check_hierarchy(interaction.user, user)
        if not can_act:
            await interaction.followup.send(embed=EmbedBuilder.error("تعذر التنفيذ", h_reason))
            return

        try:
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

                log_embed = EmbedBuilder.warning(
                    title="طرد عضو (Kick Action)",
                    description=f"تم طرد العضو {user} من السيرفر.",
                    fields=[
                        ("العضو", f"{user} (`{user.id}`)", True),
                        ("المشرف", f"{interaction.user.mention}", True),
                        ("السبب", reason, False)
                    ]
                )
                await log_svc.log_event(interaction.guild, "moderation", log_embed)

            await interaction.followup.send(embed=EmbedBuilder.success("تم طرد العضو", f"تم طرد {user.mention} بنجاح من السيرفر.\n**السبب:** {reason}"))

        except discord.Forbidden:
            await interaction.followup.send(embed=EmbedBuilder.error("صلاحيات غير كافية", "لا يمتلك البوت صلاحية طرد هذا العضو."))

    @app_commands.command(name="ban", description="حظر عضو نهائيًا من السيرفر")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(user="العضو المراد حظره", reason="سبب الحظر", delete_days="حذف الرسائل السابقة (0 إلى 7 أيام)")
    async def ban_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided", delete_days: int = 0):
        await interaction.response.defer()

        can_act, h_reason = check_hierarchy(interaction.user, user)
        if not can_act:
            await interaction.followup.send(embed=EmbedBuilder.error("تعذر التنفيذ", h_reason))
            return

        try:
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

                log_embed = EmbedBuilder.error(
                    title="حظر عضو (Ban Action)",
                    description=f"تم حظر العضو {user} من السيرفر.",
                    fields=[
                        ("العضو", f"{user} (`{user.id}`)", True),
                        ("المشرف", f"{interaction.user.mention}", True),
                        ("السبب", reason, False)
                    ]
                )
                await log_svc.log_event(interaction.guild, "moderation", log_embed)

            await interaction.followup.send(embed=EmbedBuilder.success("تم حظر العضو", f"تم حظر {user.mention} بنجاح من السيرفر.\n**السبب:** {reason}"))

        except discord.Forbidden:
            await interaction.followup.send(embed=EmbedBuilder.error("صلاحيات غير كافية", "لا يمتلك البوت صلاحية حظر هذا العضو."))

    @app_commands.command(name="unban", description="إلغاء حظر عضو باستخدام User ID")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(user_id="معرف المستخدم (User ID)", reason="السبب")
    async def unban_command(self, interaction: discord.Interaction, user_id: str, reason: str = "Unbanned by Moderator"):
        await interaction.response.defer()

        try:
            uid = int(user_id.strip())
            user = await self.bot.fetch_user(uid)
            await interaction.guild.unban(user, reason=reason)
            await interaction.followup.send(embed=EmbedBuilder.success("تم فك الحظر", f"تم إلغاء حظر المستخدم **{user}** (`{uid}`) بنجاح."))
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("تعذر إلغاء الحظر", f"حدث خطأ أثناء محاولة إلغاء الحظر: {e}"))

    @app_commands.command(name="softban", description="حظر ثم فك حظر فورًا لتطهير رسائل العضو الأخيرة")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(user="العضو المستهدف", reason="سبب الـ Softban")
    async def softban_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Softban message purge"):
        await interaction.response.defer()

        can_act, h_reason = check_hierarchy(interaction.user, user)
        if not can_act:
            await interaction.followup.send(embed=EmbedBuilder.error("تعذر التنفيذ", h_reason))
            return

        try:
            await user.ban(reason=f"Softban: {reason}", delete_message_days=1)
            await interaction.guild.unban(user, reason="Softban completion")
            await interaction.followup.send(embed=EmbedBuilder.success("تم تنفيذ Softban", f"تم طرد العضو {user.mention} وحذف رسائله الأخيرة بنجاح (يمكنه إعادة الدخول)."))
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("فشل التنفيذ", f"حدث خطأ: {e}"))

    @app_commands.command(name="purge", description="مسح عدد محدد من الرسائل في القناة الحالية")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(amount="عدد الرسائل المراد حذفها (1 إلى 100)", user="تصفية الحذف لعضو معين فقط (اختياري)")
    async def purge_command(self, interaction: discord.Interaction, amount: int, user: Optional[discord.Member] = None):
        await interaction.response.defer(ephemeral=True)

        if amount < 1 or amount > 100:
            await interaction.followup.send(embed=EmbedBuilder.error("خطأ بالقيمة", "يرجى تحديد عدد رسائل بين 1 و 100."), ephemeral=True)
            return

        def check(m):
            return user is None or m.author.id == user.id

        try:
            deleted = await interaction.channel.purge(limit=amount, check=check)
            msg = f"تم مسح **{len(deleted)}** رسالة بنجاح."
            if user:
                msg += f" (الخاصة بالعضو {user.mention})"
            await interaction.followup.send(embed=EmbedBuilder.success("تم مسح الرسائل", msg), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("فشل مسح الرسائل", f"حدث خطأ: {e}"), ephemeral=True)

    @app_commands.command(name="slowmode", description="ضبط الوضع البطيء (Slowmode) للقناة النصية")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(seconds="المدة بالثواني بين كل رسالة (0 لإلغاء Slowmode)")
    async def slowmode_command(self, interaction: discord.Interaction, seconds: int):
        await interaction.response.defer()
        if seconds < 0 or seconds > 21600:
            await interaction.followup.send(embed=EmbedBuilder.error("قيمة غير صحيحة", "الوضع البطيء يجب أن يكون بين 0 و 21600 ثانية (6 ساعات)."))
            return

        try:
            await interaction.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                embed = EmbedBuilder.success("تم إلغاء Slowmode", "تم تعطيل الوضع البطيء في هذه القناة.")
            else:
                embed = EmbedBuilder.info("تم ضبط Slowmode", f"تم ضبط فاصل الإرسال إلى **{seconds}** ثانية بين كل رسالة.")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=EmbedBuilder.error("فشل التعديل", f"حدث خطأ: {e}"))

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
