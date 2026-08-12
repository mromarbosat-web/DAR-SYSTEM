import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal
from bot.database.connection import AsyncSessionLocal
from bot.services.warning_service import WarningService
from bot.utils.hierarchy import can_moderate_member, has_warning_permission
from bot.utils.logger import logger

class WarningsCog(commands.Cog):
    """نظام التحذيرات العام المطور وإدارة العقوبات للأعضاء والإداريين"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Group for /warning subcommands
    warning_group = app_commands.Group(name="warning", description="إدارة وتفاصيل نظام التحذيرات")

    @app_commands.command(name="warn", description="إصدار تحذير عام لمستخدم (رسمي أو شفهي)")
    @app_commands.describe(
        user="العضو المراد تحذيره",
        reason="سبب التحذير",
        type="نوع التحذير (رسمي أو شفهي)",
        duration="مدة صلاحية التحذير (مثل: 1h, 1d, 1w, 1m, 3m, 6m, 1y, permanent)",
        evidence="رابط الدليل (اختياري)"
    )
    async def warn_command(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str,
        type: Literal["formal", "verbal"] = "formal",
        duration: Optional[str] = None,
        evidence: Optional[str] = None
    ):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)

            # Permission check
            if not has_warning_permission(interaction.user, "issue", settings):
                await interaction.followup.send("❌ لا تملك الصلاحيات الكافية لإصدار التحذيرات.", ephemeral=True)
                return

            # Hierarchy check
            allowed, hierarchy_msg = can_moderate_member(interaction.user, user, interaction.guild.me)
            if not allowed:
                await interaction.followup.send(f"❌ {hierarchy_msg}", ephemeral=True)
                return

            warning, punishment_msg = await service.issue_warning(
                guild=interaction.guild,
                issuer=interaction.user,
                target=user,
                reason=reason,
                warning_type=type,
                duration_str=duration,
                evidence_url=evidence
            )

            embed = discord.Embed(
                title="⚠️ تم إصدار تحذير بنجاح",
                color=discord.Color.red() if type == "formal" else discord.Color.gold(),
                timestamp=warning.created_at
            )
            embed.add_field(name="العضو المحذر", value=f"{user.mention} (`{user.id}`)", inline=True)
            embed.add_field(name="المشرف", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="نوع التحذير", value="رسمي (Formal)" if type == "formal" else "شفهي (Verbal)", inline=True)
            embed.add_field(name="معرف التحذير (ID)", value=f"`{warning.warning_id}`", inline=True)
            embed.add_field(name="السبب", value=reason, inline=False)

            if warning.expires_at:
                embed.add_field(name="ينتهي في", value=f"<t:{int(warning.expires_at.timestamp())}:R>", inline=True)
            else:
                embed.add_field(name="المدة", value="دائم", inline=True)

            if evidence:
                embed.add_field(name="الدليل", value=f"[رابط الدليل]({evidence})", inline=False)

            if punishment_msg:
                embed.add_field(name="⚠️ إجراء عقوبة تلقائي", value=punishment_msg, inline=False)

            embed.set_footer(text=f"Guild ID: {interaction.guild_id}")
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="warnings", description="عرض قائمة تحذيرات عضو")
    @app_commands.describe(
        user="العضو المراد استعراض تحذيراته (إذا ترك فارغاً يعرض تحذيراتك الخاصة)"
    )
    async def list_warnings_command(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.Member] = None
    ):
        await interaction.response.defer(ephemeral=False)
        target = user or interaction.user

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)

            if interaction.user.id != target.id:
                if not has_warning_permission(interaction.user, "view", settings):
                    await interaction.followup.send("❌ لا تملك الصلاحية لرؤية تحذيرات الأعضاء الآخرين.", ephemeral=True)
                    return

            warnings_list = await service.get_warnings(interaction.guild_id, target.id)

            if not warnings_list:
                await interaction.followup.send(f"✅ لا يوجد أي سجل تحذيرات لـ {target.mention}.")
                return

            embed = discord.Embed(
                title=f"📋 سجل تحذيرات {target.display_name}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=target.display_avatar.url)

            status_badges = {
                "ACTIVE": "🟢 نشط (ACTIVE)",
                "EXPIRED": "⚪ منتهي (EXPIRED)",
                "REMOVED": "🔴 محذوف (REMOVED)",
                "VOIDED": "🟡 ملغى (VOIDED)"
            }

            for idx, w in enumerate(warnings_list[:10], 1): # Show up to 10 newest
                moderator = interaction.guild.get_member(w.moderator_id)
                mod_str = moderator.mention if moderator else f"`{w.moderator_id}`"
                status_str = status_badges.get(w.status, w.status)
                type_str = "رسمي" if w.warning_type == "formal" else "شفهي"

                exp_str = f"<t:{int(w.expires_at.timestamp())}:R>" if w.expires_at else "دائم"

                embed.add_field(
                    name=f"#{idx} | ID: `{w.warning_id[:8]}` ({type_str}) - {status_str}",
                    value=f"**السبب:** {w.reason}\n**المشرف:** {mod_str}\n**الانتهاء:** {exp_str}\n**التاريخ:** <t:{int(w.created_at.timestamp())}:D>",
                    inline=False
                )

            embed.set_footer(text=f"إجمالي التحذيرات: {len(warnings_list)} | Guild ID: {interaction.guild_id}")
            await interaction.followup.send(embed=embed)

    @warning_group.command(name="view", description="عرض تفاصيل تحذير محدد باستخدام المعرف")
    @app_commands.describe(warning_id="معرف التحذير (ID)")
    async def view_warning_subcommand(self, interaction: discord.Interaction, warning_id: str):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not has_warning_permission(interaction.user, "view", settings):
                await interaction.followup.send("❌ لا تملك الصلاحيات لمشاهدة تفاصيل التحذيرات.", ephemeral=True)
                return

            warning = await service.get_warning_by_id(interaction.guild_id, warning_id)
            if not warning:
                await interaction.followup.send("❌ لم يتم العثور على تحذير بهذا المعرف.", ephemeral=True)
                return

            target = interaction.guild.get_member(warning.user_id)
            mod = interaction.guild.get_member(warning.moderator_id)

            embed = discord.Embed(
                title=f"🔍 تفاصيل التحذير | ID: `{warning.warning_id}`",
                color=discord.Color.dark_teal(),
                timestamp=warning.created_at
            )
            embed.add_field(name="العضو المحذر", value=target.mention if target else f"`{warning.user_id}`", inline=True)
            embed.add_field(name="المشرف", value=mod.mention if mod else f"`{warning.moderator_id}`", inline=True)
            embed.add_field(name="النوع", value="رسمي" if warning.warning_type == "formal" else "شفهي", inline=True)
            embed.add_field(name="الحالة الحالية", value=warning.status, inline=True)
            embed.add_field(name="السبب", value=warning.reason, inline=False)

            if warning.expires_at:
                embed.add_field(name="تاريخ الانتهاء", value=f"<t:{int(warning.expires_at.timestamp())}:f>", inline=True)
            else:
                embed.add_field(name="المدة", value="دائم", inline=True)

            if warning.evidence_url:
                embed.add_field(name="رابط الدليل الرئيسية", value=f"[رابط الدليل]({warning.evidence_url})", inline=False)

            if warning.evidences:
                evidence_text = "\n".join([f"• [{e.note or 'دليل'}]({e.content_url})" for e in warning.evidences])
                embed.add_field(name="الأدلة المرفقة", value=evidence_text, inline=False)

            if warning.edit_history:
                embed.add_field(name="تاريخ التعديلات", value="تم تعديل هذا التحذير مسبقًا.", inline=False)

            if warning.removal_reason:
                embed.add_field(name="سبب الحذف/الإلغاء", value=warning.removal_reason, inline=False)

            await interaction.followup.send(embed=embed)

    @warning_group.command(name="edit", description="تعديل سبب أو دليل أو مدة تحذير قائم")
    @app_commands.describe(
        warning_id="معرف التحذير (ID)",
        reason="السبب الجديد (اختياري)",
        evidence="رابط الدليل الجديد (اختياري)",
        duration="المدة الجديدة (اختياري)"
    )
    async def edit_warning_subcommand(
        self,
        interaction: discord.Interaction,
        warning_id: str,
        reason: Optional[str] = None,
        evidence: Optional[str] = None,
        duration: Optional[str] = None
    ):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not has_warning_permission(interaction.user, "edit", settings):
                await interaction.followup.send("❌ لا تملك الصلاحية لتعديل التحذيرات.", ephemeral=True)
                return

            updated_warning = await service.edit_warning(
                guild_id=interaction.guild_id,
                warning_id=warning_id,
                editor_id=interaction.user.id,
                new_reason=reason,
                new_evidence=evidence,
                new_duration_str=duration
            )

            if not updated_warning:
                await interaction.followup.send("❌ لم يتم العثور على التحذير المطلوب لتعديله.", ephemeral=True)
                return

            await interaction.followup.send(f"✅ تم تعديل التحذير `{warning_id}` بنجاح.")

    @warning_group.command(name="remove", description="حذف أو إلغاء تحذير")
    @app_commands.describe(
        warning_id="معرف التحذير (ID)",
        reason="سبب الحذف/الإلغاء",
        void="إلغاء كلي للتحذير بدلاً من إزالته العادية"
    )
    async def remove_warning_subcommand(
        self,
        interaction: discord.Interaction,
        warning_id: str,
        reason: str,
        void: bool = False
    ):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not has_warning_permission(interaction.user, "remove", settings):
                await interaction.followup.send("❌ لا تملك الصلاحية لحذف التحذيرات.", ephemeral=True)
                return

            res = await service.remove_warning(
                guild_id=interaction.guild_id,
                warning_id=warning_id,
                remover_id=interaction.user.id,
                reason=reason,
                void=void
            )

            if not res:
                await interaction.followup.send("❌ لم يتم العثور على التحذير المطلوب.", ephemeral=True)
                return

            action_str = "إلغاء (VOIDED)" if void else "حذف (REMOVED)"
            await interaction.followup.send(f"✅ تم {action_str} التحذير `{warning_id}` بنجاح.\nالسبب: {reason}")

    @warning_group.command(name="expire", description="إنهاء صلاحية تحذير نشط فوراً")
    @app_commands.describe(warning_id="معرف التحذير (ID)")
    async def expire_warning_subcommand(self, interaction: discord.Interaction, warning_id: str):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not has_warning_permission(interaction.user, "expire", settings):
                await interaction.followup.send("❌ لا تملك الصلاحية لإنهاء صلاحية التحذيرات.", ephemeral=True)
                return

            res = await service.force_expire_warning(interaction.guild_id, warning_id)
            if not res:
                await interaction.followup.send("❌ لم يتم العثور على التحذير المطلوب.", ephemeral=True)
                return

            await interaction.followup.send(f"✅ تم تغيير حالة التحذير `{warning_id}` إلى منتهي الصلاحية (EXPIRED).")

    @warning_group.command(name="settings", description="ضبط إعدادات نظام التحذيرات والرتب والصلاحيات")
    @app_commands.describe(
        issuer_role="رتبة محذري الأعضاء",
        viewer_role="رتبة مستعرضي التحذيرات",
        editor_role="رتبة معدلي التحذيرات",
        remover_role="رتبة حذفي التحذيرات",
        expirer_role="رتبة إنهائي التحذيرات",
        evidence_channel="روم تسجيل أدلة التحذيرات",
        default_duration="المدة الافتراضية للتحذير",
        demotion_threshold="عدد التحذيرات الرسمية لتطبيق العقوبة الآلية",
        demotion_action="نوع العقوبة عند تجاوز الحد"
    )
    async def warning_settings_subcommand(
        self,
        interaction: discord.Interaction,
        issuer_role: Optional[discord.Role] = None,
        viewer_role: Optional[discord.Role] = None,
        editor_role: Optional[discord.Role] = None,
        remover_role: Optional[discord.Role] = None,
        expirer_role: Optional[discord.Role] = None,
        evidence_channel: Optional[discord.TextChannel] = None,
        default_duration: Optional[str] = None,
        demotion_threshold: Optional[int] = None,
        demotion_action: Optional[Literal["remove_roles", "timeout", "kick"]] = None
    ):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not has_warning_permission(interaction.user, "settings", settings):
                await interaction.followup.send("❌ لا تملك الصلاحية لتعديل إعدادات التحذيرات.", ephemeral=True)
                return

            updates = {}
            if issuer_role: updates["issuer_role_id"] = issuer_role.id
            if viewer_role: updates["viewer_role_id"] = viewer_role.id
            if editor_role: updates["editor_role_id"] = editor_role.id
            if remover_role: updates["remover_role_id"] = remover_role.id
            if expirer_role: updates["expirer_role_id"] = expirer_role.id
            if evidence_channel: updates["evidence_channel_id"] = evidence_channel.id
            if default_duration: updates["default_warning_duration"] = default_duration
            if demotion_threshold is not None: updates["staff_demotion_threshold"] = demotion_threshold
            if demotion_action: updates["demotion_action"] = demotion_action

            if not updates:
                # Display current settings
                embed = discord.Embed(
                    title="⚙️ إعدادات نظام التحذيرات الحالية",
                    color=discord.Color.purple(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="رتبة المحذرين", value=f"<@&{settings.issuer_role_id}>" if settings.issuer_role_id else "افتراضي (Moderate Members)", inline=True)
                embed.add_field(name="رتبة المستعرضين", value=f"<@&{settings.viewer_role_id}>" if settings.viewer_role_id else "افتراضي", inline=True)
                embed.add_field(name="رتبة الحاذفين", value=f"<@&{settings.remover_role_id}>" if settings.remover_role_id else "افتراضي (Administrator)", inline=True)
                embed.add_field(name="قناة الأدلة", value=f"<#{settings.evidence_channel_id}>" if settings.evidence_channel_id else "غير محددة", inline=True)
                embed.add_field(name="المدة الافتراضية", value=settings.default_warning_duration, inline=True)
                embed.add_field(name="حد عقوبة التجريد", value=f"{settings.staff_demotion_threshold} تحذيرات", inline=True)
                embed.add_field(name="نوع العقوبة الآلية", value=settings.demotion_action, inline=True)
                await interaction.followup.send(embed=embed)
                return

            new_settings = await service.update_settings(interaction.guild_id, **updates)
            await interaction.followup.send("✅ تم تحديث إعدادات نظام التحذيرات بنجاح.")

async def setup(bot: commands.Bot):
    await bot.add_cog(WarningsCog(bot))
