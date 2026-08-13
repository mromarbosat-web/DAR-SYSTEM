import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal, Union
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
        user: Union[discord.Member, discord.User],
        reason: str,
        type: Literal["formal", "verbal"] = "formal",
        duration: Optional[str] = None,
        evidence: Optional[str] = None
    ):
        await interaction.response.defer(ephemeral=False)

        if not interaction.guild:
            await interaction.followup.send("❌ هذا الأمر مخصص للاستخدام داخل السيرفرات فقط.", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)

            # Permission check
            if not await has_warning_permission(interaction.user, "issue", settings, session):
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

            # Send DM to the warned user
            dm_embed = discord.Embed(
                title=f"⚠️ تلقيت تحذيراً {'رسمياً' if type == 'formal' else 'شفهياً'}",
                description=f"لقد تلقيت تحذيراً في سيرفر **{interaction.guild.name}**.\n\n"
                            f"**السبب:** `{reason}`\n"
                            f"**بواسطة:** {interaction.user.display_name}\n"
                            f"**رقم التحذير:** `#{warning.local_id}`",
                color=discord.Color.red() if type == "formal" else discord.Color.gold()
            )
            if warning.expires_at:
                dm_embed.add_field(name="ينتهي في", value=f"<t:{int(warning.expires_at.timestamp())}:f>", inline=False)
            else:
                dm_embed.add_field(name="المدة", value="دائم", inline=False)
            
            dm_embed.add_field(name="💡 نصيحة", value="تكرار المخالفات قد يؤدي لعقوبات آلية مثل (العزل المؤقت، الطرد، أو الحظر). يرجى مراجعة قوانين السيرفر.", inline=False)
            
            try: await user.send(embed=dm_embed)
            except: pass

            embed = discord.Embed(
                title="⚠️ تم إصدار تحذير بنجاح",
                color=discord.Color.red() if type == "formal" else discord.Color.gold(),
                timestamp=warning.created_at or discord.utils.utcnow()
            )
            embed.add_field(name="العضو المحذر", value=f"{user.mention} (`{user.id}`)", inline=True)
            embed.add_field(name="المشرف", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="نوع التحذير", value="رسمي (Formal)" if type == "formal" else "شفهي (Verbal)", inline=True)
            embed.add_field(name="رقم التحذير (#)", value=f"`{warning.local_id}`", inline=True)
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
                if not await has_warning_permission(interaction.user, "view", settings, session):
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

            for w in warnings_list[:10]: # Show up to 10 newest
                moderator = interaction.guild.get_member(w.moderator_id)
                mod_str = moderator.mention if moderator else f"`{w.moderator_id}`"
                status_str = status_badges.get(w.status, w.status)
                type_str = "رسمي" if w.warning_type == "formal" else "شفهي"

                exp_str = f"<t:{int(w.expires_at.timestamp())}:R>" if w.expires_at else "دائم"

                embed.add_field(
                    name=f"#{w.local_id} | ({type_str}) - {status_str}",
                    value=f"**السبب:** {w.reason}\n**المشرف:** {mod_str}\n**الانتهاء:** {exp_str}\n**التاريخ:** <t:{int(w.created_at.timestamp())}:D>",
                    inline=False
                )

            embed.set_footer(text=f"إجمالي التحذيرات: {len(warnings_list)} | Guild ID: {interaction.guild_id}")
            await interaction.followup.send(embed=embed)

    @warning_group.command(name="view", description="عرض تفاصيل تحذير محدد")
    @app_commands.describe(user="العضو صاحب التحذير", local_id="رقم التحذير (مثال: 1)")
    async def view_warning_subcommand(self, interaction: discord.Interaction, user: discord.Member, local_id: int):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not await has_warning_permission(interaction.user, "view", settings, session):
                await interaction.followup.send("❌ لا تملك الصلاحيات لمشاهدة تفاصيل التحذيرات.", ephemeral=True)
                return

            warning = await service.get_warning_by_local_id(interaction.guild_id, user.id, local_id)
            if not warning:
                await interaction.followup.send("❌ لم يتم العثور على تحذير بهذا الرقم للعضو المحدد.", ephemeral=True)
                return

            mod = interaction.guild.get_member(warning.moderator_id)

            embed = discord.Embed(
                title=f"🔍 تفاصيل التحذير | #{warning.local_id}",
                color=discord.Color.dark_teal(),
                timestamp=warning.created_at
            )
            embed.add_field(name="العضو المحذر", value=user.mention, inline=True)
            embed.add_field(name="المشرف", value=mod.mention if mod else f"`{warning.moderator_id}`", inline=True)
            embed.add_field(name="النوع", value="رسمي" if warning.warning_type == "formal" else "شفهي", inline=True)
            embed.add_field(name="الحالة الحالية", value=warning.status, inline=True)
            embed.add_field(name="السبب", value=warning.reason, inline=False)
            embed.add_field(name="UUID", value=f"`{warning.warning_id}`", inline=False)

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
        user="العضو صاحب التحذير",
        local_id="رقم التحذير (مثال: 1)",
        reason="السبب الجديد (اختياري)",
        evidence="رابط الدليل الجديد (اختياري)",
        duration="المدة الجديدة (اختياري)"
    )
    async def edit_warning_subcommand(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        local_id: int,
        reason: Optional[str] = None,
        evidence: Optional[str] = None,
        duration: Optional[str] = None
    ):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not await has_warning_permission(interaction.user, "edit", settings, session):
                await interaction.followup.send("❌ لا تملك الصلاحية لتعديل التحذيرات.", ephemeral=True)
                return

            updated_warning = await service.edit_warning(
                guild_id=interaction.guild_id,
                user_id=user.id,
                local_id=local_id,
                editor_id=interaction.user.id,
                new_reason=reason,
                new_evidence=evidence,
                new_duration_str=duration
            )

            if not updated_warning:
                await interaction.followup.send("❌ لم يتم العثور على التحذير المطلوب لتعديله.", ephemeral=True)
                return

            await interaction.followup.send(f"✅ تم تعديل التحذير #{local_id} للعضو {user.mention} بنجاح.")

    @warning_group.command(name="remove", description="حذف أو إلغاء تحذير")
    @app_commands.describe(
        user="العضو صاحب التحذير",
        local_id="رقم التحذير (مثال: 1)",
        reason="سبب الحذف/الإلغاء",
        void="إلغاء كلي للتحذير بدلاً من إزالته العادية"
    )
    async def remove_warning_subcommand(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        local_id: int,
        reason: str,
        void: bool = False
    ):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not await has_warning_permission(interaction.user, "remove", settings, session):
                await interaction.followup.send("❌ لا تملك الصلاحية لحذف التحذيرات.", ephemeral=True)
                return

            res = await service.remove_warning(
                guild_id=interaction.guild_id,
                user_id=user.id,
                local_id=local_id,
                remover_id=interaction.user.id,
                reason=reason,
                void=void
            )

            if not res:
                await interaction.followup.send("❌ لم يتم العثور على التحذير المطلوب.", ephemeral=True)
                return

            action_str = "إلغاء (VOIDED)" if void else "حذف (REMOVED)"
            await interaction.followup.send(f"✅ تم {action_str} التحذير #{local_id} للعضو {user.mention} بنجاح.\nالسبب: {reason}")

    @warning_group.command(name="expire", description="إنهاء صلاحية تحذير نشط فوراً")
    @app_commands.describe(user="العضو صاحب التحذير", local_id="رقم التحذير (مثال: 1)")
    async def expire_warning_subcommand(self, interaction: discord.Interaction, user: discord.Member, local_id: int):
        await interaction.response.defer(ephemeral=False)

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)

            if not await has_warning_permission(interaction.user, "expire", settings, session):
                await interaction.followup.send("❌ لا تملك الصلاحية لإنهاء صلاحية التحذيرات.", ephemeral=True)
                return

            res = await service.force_expire_warning(interaction.guild_id, user.id, local_id)
            if not res:
                await interaction.followup.send("❌ لم يتم العثور على التحذير المطلوب.", ephemeral=True)
                return

            await interaction.followup.send(f"✅ تم تغيير حالة التحذير #{local_id} للعضو {user.mention} إلى منتهي الصلاحية (EXPIRED).")

    @warning_group.command(name="activate", description="إعادة تفعيل تحذير غير نشط")
    @app_commands.describe(user="العضو صاحب التحذير", local_id="رقم التحذير (مثال: 1)")
    async def activate_warning_subcommand(self, interaction: discord.Interaction, user: discord.Member, local_id: int):
        await interaction.response.defer(ephemeral=False)
        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)
            if not await has_warning_permission(interaction.user, "edit", settings, session):
                await interaction.followup.send("❌ لا تملك الصلاحية لتعديل حالات التحذيرات.", ephemeral=True)
                return
            res = await service.activate_warning(interaction.guild_id, user.id, local_id)
            if not res:
                await interaction.followup.send("❌ لم يتم العثور على التحذير.", ephemeral=True)
                return
            await interaction.followup.send(f"✅ تم إعادة تفعيل التحذير #{local_id} للعضو {user.mention} بنجاح.")

    @warning_group.command(name="delete-permanently", description="حذف تحذير نهائياً من قاعدة البيانات")
    @app_commands.describe(user="العضو صاحب التحذير", local_id="رقم التحذير (مثال: 1)")
    async def delete_permanent_subcommand(self, interaction: discord.Interaction, user: discord.Member, local_id: int):
        await interaction.response.defer(ephemeral=False)
        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            settings = await service.get_settings(interaction.guild_id)
            if not await has_warning_permission(interaction.user, "remove", settings, session):
                await interaction.followup.send("❌ لا تملك الصلاحية للحذف النهائي للتحذيرات.", ephemeral=True)
                return
            res = await service.delete_warning_permanently(interaction.guild_id, user.id, local_id)
            if not res:
                await interaction.followup.send("❌ لم يتم العثور على التحذير.", ephemeral=True)
                return
            await interaction.followup.send(f"✅ تم حذف التحذير #{local_id} للعضو {user.mention} نهائياً.")

    @warning_group.command(name="clear-all", description="حذف كافة التحذيرات لسيرفر أو عضو محدد")
    @app_commands.describe(user="العضو المراد تصفير تحذيراته (اختياري، اتركه فارغاً لتصفير السيرفر بالكامل)")
    async def clear_all_subcommand(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        await interaction.response.defer(ephemeral=False)
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ هذا الأمر يتطلب صلاحيات مدير السيرفر (Administrator).", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            service = WarningService(session)
            count = await service.delete_all_warnings(interaction.guild_id, user.id if user else None)
            target_str = user.mention if user else "السيرفر بالكامل"
            await interaction.followup.send(f"✅ تم تصفير كافة التحذيرات لـ {target_str} بنجاح. (إجمالي المحذوف: {count})")

    @warning_group.command(name="permission", description="تحديد صلاحية مخصصة لرتبة معينة (تشمل كافة أوامر البوت)")
    @app_commands.describe(
        role="الرتبة المراد إعطاؤها الصلاحية",
        permission_type="نوع الصلاحية",
        action="إضافة أو إزالة"
    )
    @app_commands.choices(
        permission_type=[
            app_commands.Choice(name="Issue Warnings (إصدار تحذيرات)", value="WARNING_ISSUE"),
            app_commands.Choice(name="Remove/Clear Warnings (حذف وتصفير تحذيرات)", value="WARNING_REMOVE"),
            app_commands.Choice(name="View Warnings (عرض تحذيرات)", value="WARNING_VIEW"),
            app_commands.Choice(name="Timeout Members (عزل أعضاء)", value="MOD_TIMEOUT"),
            app_commands.Choice(name="Kick Members (طرد أعضاء)", value="MOD_KICK"),
            app_commands.Choice(name="Ban Members (حظر أعضاء)", value="MOD_BAN"),
            app_commands.Choice(name="Purge Messages (مسح رسائل)", value="MOD_PURGE"),
            app_commands.Choice(name="Lock/Unlock Channels (قفل وفتح الرومات)", value="MOD_LOCK_UNLOCK"),
            app_commands.Choice(name="Voice Move/Disconnect (نقل وفصل صوتي)", value="VOICE_MANAGER"),
        ],
        action=[
            app_commands.Choice(name="Grant (إعطاء)", value="grant"),
            app_commands.Choice(name="Revoke (سحب)", value="revoke")
        ]
    )
    async def warning_permission_subcommand(
        self, 
        interaction: discord.Interaction, 
        role: discord.Role, 
        permission_type: app_commands.Choice[str],
        action: Literal["grant", "revoke"]
    ):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ هذا الأمر يتطلب صلاحيات مدير السيرفر.", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            from bot.database.repositories.permission_repository import PermissionRepository
            repo = PermissionRepository(session)
            if action == "grant":
                await repo.add_permission_role(interaction.guild_id, permission_type.value, role.id)
                msg = f"✅ تم إعطاء رتبة {role.mention} صلاحية `{permission_type.name}` بنجاح."
            else:
                await repo.remove_permission_role(interaction.guild_id, permission_type.value, role.id)
                msg = f"✅ تم سحب صلاحية `{permission_type.name}` من رتبة {role.mention}."
            
            await interaction.followup.send(msg, ephemeral=True)

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

            if not await has_warning_permission(interaction.user, "settings", settings, session):
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
