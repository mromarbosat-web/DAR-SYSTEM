import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from bot.config.settings import settings
from bot.database.connection import AsyncSessionLocal
from bot.services.economy_service import EconomyService
from bot.services.log_service import LogService
from bot.services.shop_service import ShopService
from bot.utils.embeds import EmbedBuilder

class TransferConfirmation(discord.ui.View):
    def __init__(self, from_user, to_user, amount, timeout=60):
        super().__init__(timeout=timeout)
        self.from_user = from_user
        self.to_user = to_user
        self.amount = amount
        self.value = None

    @discord.ui.button(label="تأكيد التحويل", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.from_user.id:
            await interaction.response.send_message("❌ هذا الزر ليس لك!", ephemeral=True)
            return
        self.value = True
        self.stop()
        await interaction.response.edit_message(view=None)

    @discord.ui.button(label="إلغاء", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.from_user.id:
            await interaction.response.send_message("❌ هذا الزر ليس لك!", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.edit_message(content="❌ تم إلغاء عملية التحويل.", embed=None, view=None)

class EconomyCog(commands.Cog):
    """Cog for User Economy & Admin Economy Commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    eco_group = app_commands.Group(name="economy", description="إدارة واحصائيات نظام الاقتصاد وإعدادات العملة")

    @app_commands.command(name="balance", description="عرض رصيدك الحالي في المحفظة والبنك")
    @app_commands.describe(user="العضو المراد استعلام رصيده (اختياري)")
    async def balance_command(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        await interaction.response.defer()
        target = user or interaction.user

        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            bal, bank_bal, total = await eco_service.get_balance(target.id)

            fields = [
                ("👛 رصيد المحفظة", f"`{bal:,}` {settings.CURRENCY_NAME}", True),
                ("🏦 رصيد البنك", f"`{bank_bal:,}` {settings.CURRENCY_NAME}", True),
                ("💎 إجمالي الثروة", f"`{total:,}` {settings.CURRENCY_NAME}", True),
            ]

            embed = EmbedBuilder.info(
                title=f"رصيد الاقتصاد - {target.display_name}",
                description=f"استعلام الرصيد للعملة العالمية **{settings.CURRENCY_NAME}** {settings.CURRENCY_EMOJI}",
                fields=fields
            )
            embed.set_footer(text=f"User ID: {target.id}")
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="daily", description="المطالبة بالمكافأة اليومية مع مكافأة الاستمرارية (Streak)")
    async def daily_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            success, msg, reward, streak = await eco_service.claim_daily(
                user_id=interaction.user.id,
                guild_id=interaction.guild.id if interaction.guild else settings.MAIN_GUILD_ID
            )
            if success:
                log_svc = LogService(session)
                embed_log = discord.Embed(title="💰 مكافأة يومية", color=discord.Color.green())
                embed_log.add_field(name="العضو", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
                embed_log.add_field(name="المبلغ", value=f"`{reward}`", inline=True)
                embed_log.add_field(name="الـ Streak", value=f"`{streak}`", inline=True)
                await log_svc.log_event(interaction.guild, "economy", embed_log)


            if success:
                embed = EmbedBuilder.success(
                    title="المكافأة اليومية (Daily Claim)",
                    description=msg,
                    fields=[
                        ("المبلغ المحصل", f"`+{reward:,}` {settings.CURRENCY_NAME}", True),
                        ("أيام الاستمرارية (Streak)", f"`{streak}` يوم متتالي 🔥", True)
                    ]
                )
            else:
                embed = EmbedBuilder.warning("المكافأة اليومية غير متاحة", msg)

            await interaction.followup.send(embed=embed)

    @app_commands.command(name="pay", description="تحويل مبلغ مالي من حسابك إلى عضو آخر")
    @app_commands.describe(user="العضو المستلم", amount="المبلغ المراد تحويله")
    async def pay_command(self, interaction: discord.Interaction, user: discord.User, amount: int):
        if amount <= 0:
            await interaction.response.send_message(embed=EmbedBuilder.error("خطأ", "المبلغ يجب أن يكون أكبر من صفر!"), ephemeral=True)
            return
        
        if user.id == interaction.user.id:
            await interaction.response.send_message(embed=EmbedBuilder.error("خطأ", "لا يمكنك التحويل لنفسك!"), ephemeral=True)
            return

        if user.bot:
            await interaction.response.send_message(embed=EmbedBuilder.error("خطأ", "لا يمكنك التحويل للبوتات!"), ephemeral=True)
            return

        # Confirmation step
        confirm_embed = EmbedBuilder.info(
            title="تأكيد عملية التحويل",
            description=f"هل أنت متأكد من رغبتك في تحويل **{amount:,}** {settings.CURRENCY_NAME} إلى {user.mention}؟"
        )
        view = TransferConfirmation(interaction.user, user, amount)
        await interaction.response.send_message(embed=confirm_embed, view=view)
        
        await view.wait()
        if view.value is not True:
            return

        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            success, msg = await eco_service.transfer_coins(
                from_user=interaction.user,
                to_user=user,
                amount=amount,
                guild_id=interaction.guild.id if interaction.guild else None
            )
            
            if success:
                log_svc = LogService(session)
                embed_log = discord.Embed(title="💸 تحويل رصيد", color=discord.Color.blue())
                embed_log.add_field(name="المرسل", value=f"{interaction.user.mention}", inline=True)
                embed_log.add_field(name="المستلم", value=f"{user.mention}", inline=True)
                embed_log.add_field(name="المبلغ", value=f"`{amount}`", inline=False)
                await log_svc.log_event(interaction.guild, "economy", embed_log)

                # Send DMs
                dm_embed_sender = EmbedBuilder.info(
                    title="💸 تأكيد تحويل رصيد",
                    description=f"لقد قمت بتحويل **{amount:,}** {settings.CURRENCY_NAME} بنجاح إلى {user.mention}."
                )
                dm_embed_receiver = EmbedBuilder.success(
                    title="💰 وصول حوالة مالية",
                    description=f"لقد استلمت حوالة بقيمة **{amount:,}** {settings.CURRENCY_NAME} من {interaction.user.mention}."
                )
                
                try: await interaction.user.send(embed=dm_embed_sender)
                except: pass
                try: await user.send(embed=dm_embed_receiver)
                except: pass

                final_embed = EmbedBuilder.success(
                    title="تم تحويل المبلغ",
                    description=f"تم تحويل `{amount:,}` {settings.CURRENCY_NAME} من {interaction.user.mention} إلى {user.mention} بنجاح."
                )
            else:
                final_embed = EmbedBuilder.error("فشل التحويل", msg)

            await interaction.edit_original_response(embed=final_embed, view=None)

    @app_commands.command(name="deposit", description="إيداع مبلغ من المحفظة إلى حساب البنك")
    @app_commands.describe(amount="المبلغ المراد إيداعه (أو اكتب 'all' لإيداع كل الرصيد)")
    async def deposit_command(self, interaction: discord.Interaction, amount: str):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            bal, bank_bal, _ = await eco_service.get_balance(interaction.user.id)

            if amount.lower().strip() == "all":
                dep_amount = bal
            else:
                try:
                    dep_amount = int(amount)
                except ValueError:
                    await interaction.followup.send(embed=EmbedBuilder.error("خطأ", "يرجى كتابة رقم صحيح أو `all` للإيداع!"))
                    return

            success, msg, new_bal, new_bank = await eco_service.deposit(interaction.user.id, dep_amount)

            if success:
                embed = EmbedBuilder.success(
                    title="تم الإيداع في البنك",
                    description=msg,
                    fields=[
                        ("رصيد المحفظة المتبقي", f"`{new_bal:,}` {settings.CURRENCY_NAME}", True),
                        ("رصيد البنك الجديد", f"`{new_bank:,}` {settings.CURRENCY_NAME}", True)
                    ]
                )
            else:
                embed = EmbedBuilder.error("فشل الإيداع", msg)

            await interaction.followup.send(embed=embed)

    @app_commands.command(name="withdraw", description="سحب مبلغ من البنك إلى المحفظة")
    @app_commands.describe(amount="المبلغ المراد سحبه (أو اكتب 'all' لسحب كل رصيد البنك)")
    async def withdraw_command(self, interaction: discord.Interaction, amount: str):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            bal, bank_bal, _ = await eco_service.get_balance(interaction.user.id)

            if amount.lower().strip() == "all":
                with_amount = bank_bal
            else:
                try:
                    with_amount = int(amount)
                except ValueError:
                    await interaction.followup.send(embed=EmbedBuilder.error("خطأ", "يرجى كتابة رقم صحيح أو `all` للسحب!"))
                    return

            success, msg, new_bal, new_bank = await eco_service.withdraw(interaction.user.id, with_amount)

            if success:
                embed = EmbedBuilder.success(
                    title="تم السحب من البنك",
                    description=msg,
                    fields=[
                        ("رصيد المحفظة الجديد", f"`{new_bal:,}` {settings.CURRENCY_NAME}", True),
                        ("رصيد البنك المتبقي", f"`{new_bank:,}` {settings.CURRENCY_NAME}", True)
                    ]
                )
            else:
                embed = EmbedBuilder.error("فشل السحب", msg)

            await interaction.followup.send(embed=embed)

    @app_commands.command(name="leaderboard", description="عرض لائحة أغنى الأعضاء في الاقتصاد")
    async def leaderboard_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            top_users = await eco_service.get_leaderboard(limit=10, include_bank=True)

            if not top_users:
                embed = EmbedBuilder.info("لائحة المتصدرين", "لا توجد بيانات مالية مسجلة بعد.")
            else:
                lines = []
                for idx, (uid, total_bal) in enumerate(top_users, start=1):
                    medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"`#{idx}`"
                    lines.append(f"{medal} <@{uid}> — **{total_bal:,}** {settings.CURRENCY_NAME}")

                embed = EmbedBuilder.info(
                    title="🏆 لائحة أثرياء السيرفر (Economy Leaderboard)",
                    description="\n".join(lines)
                )

            await interaction.followup.send(embed=embed)

    @app_commands.command(name="inventory", description="عرض المنتجات والأغراض الممتازة المملوكة للمستخدم")
    @app_commands.describe(user="العضو المراد عرض حقيبته (اختياري)")
    async def inventory_command(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        await interaction.response.defer()
        target = user or interaction.user

        async with AsyncSessionLocal() as session:
            shop_service = ShopService(session)
            items = await shop_service.get_user_inventory(target.id)

            if not items:
                embed = EmbedBuilder.info(
                    title=f"حقيبة المشتريات - {target.display_name}",
                    description="الحقيبة فارغة، لا توجد منتجات مملوكة حاليًا."
                )
            else:
                fields = []
                for prod, qty in items:
                    fields.append((
                        f"{prod.emoji} {prod.name}",
                        f"**الكمية:** `{qty}` | **النوع:** `{prod.type}` | **معرف المنتج:** `#{prod.product_id}`",
                        False
                    ))

                embed = EmbedBuilder.info(
                    title=f"🎒 حقيبة المشتريات - {target.display_name}",
                    description=f"جميع الأغراض والرتب التي قام بابتياعها من متجر {settings.CURRENCY_NAME}:",
                    fields=fields
                )

            await interaction.followup.send(embed=embed)

    @eco_group.command(name="average", description="حساب متوسط ثروة عملة سراب لجميع الحسابات الحقيقية")
    @app_commands.describe(include_bank="تضمين أرصدة الحسابات البنكية في الحساب (افتراضيًا نعم)")
    async def average_command(self, interaction: discord.Interaction, include_bank: bool = True):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            bot_ids = [self.bot.user.id] if self.bot.user else []
            count, total, avg = await eco_service.get_average(include_bank=include_bank, bot_user_ids=bot_ids)

            fields = [
                ("👥 الحسابات المساهمة", f"`{count:,}` حساب نشط", True),
                ("💰 إجمالي السيولة العالمية", f"`{total:,}` {settings.CURRENCY_NAME}", True),
                ("📊 متوسط ثروة الحساب", f"`{avg:,.2f}` {settings.CURRENCY_NAME}", True)
            ]

            embed = EmbedBuilder.info(
                title="📊 إحصائيات ومتوسط ثروة الاقتصاد العالمية",
                description="تحليل وتوزيع العملة عبر قاعدة البيانات (استثناء حسابات البوتات):",
                fields=fields
            )
            await interaction.followup.send(embed=embed)

    # --- ADMIN ECONOMY COMMANDS ---

    @eco_group.command(name="give", description="[إداري] منح مبلغ مالية لعضو محدد")
    @app_commands.describe(user="العضو المستهدف", amount="المبلغ الممنوح", reason="السبب الإداري")
    async def admin_give(self, interaction: discord.Interaction, user: discord.User, amount: int, reason: str = "Admin Grant"):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            success, msg = await eco_service.admin_modify_balance(
                admin_member=interaction.user,
                target_user=user,
                action="give",
                amount=amount,
                reason=reason,
                guild_id=interaction.guild.id if interaction.guild else None
            )

            if success:
                embed = EmbedBuilder.success("تم الإيداع الإداري", msg)
            else:
                embed = EmbedBuilder.error("فشلت العملية", msg)

            await interaction.followup.send(embed=embed, ephemeral=True)

    @eco_group.command(name="remove", description="[إداري] خصم مبلغ مالي من حساب عضو")
    @app_commands.describe(user="العضو المستهدف", amount="المبلغ المراد خصمه", reason="السبب الإداري")
    async def admin_remove(self, interaction: discord.Interaction, user: discord.User, amount: int, reason: str = "Admin Deduction"):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            success, msg = await eco_service.admin_modify_balance(
                admin_member=interaction.user,
                target_user=user,
                action="remove",
                amount=amount,
                reason=reason,
                guild_id=interaction.guild.id if interaction.guild else None
            )

            if success:
                embed = EmbedBuilder.success("تم الخصم الإداري", msg)
            else:
                embed = EmbedBuilder.error("فشلت العملية", msg)

            await interaction.followup.send(embed=embed, ephemeral=True)

    @eco_group.command(name="set", description="[إداري] تعيين رصيد محدد مباشرة لحساب عضو")
    @app_commands.describe(user="العضو المستهدف", amount="الرصيد الجديد المستهدف", reason="السبب الإداري")
    async def admin_set(self, interaction: discord.Interaction, user: discord.User, amount: int, reason: str = "Admin Set Balance"):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            success, msg = await eco_service.admin_modify_balance(
                admin_member=interaction.user,
                target_user=user,
                action="set",
                amount=amount,
                reason=reason,
                guild_id=interaction.guild.id if interaction.guild else None
            )

            if success:
                embed = EmbedBuilder.success("تم تعيين الرصيد", msg)
            else:
                embed = EmbedBuilder.error("فشلت العملية", msg)

            await interaction.followup.send(embed=embed, ephemeral=True)

    @eco_group.command(name="reset", description="[إداري] تصفير رصيد عضو بالكامل")
    @app_commands.describe(user="العضو المستهدف")
    async def admin_reset(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            success, msg = await eco_service.admin_modify_balance(
                admin_member=interaction.user,
                target_user=user,
                action="reset",
                amount=0,
                reason="Admin Reset Balance",
                guild_id=interaction.guild.id if interaction.guild else None
            )

            if success:
                embed = EmbedBuilder.success("تم تصفير الرصيد", msg)
            else:
                embed = EmbedBuilder.error("فشلت العملية", msg)

            await interaction.followup.send(embed=embed, ephemeral=True)

    @eco_group.command(name="settings", description="[إداري] تخصيص قيم ومكافآت وتكافؤات نظام الاقتصاد")
    @app_commands.describe(
        daily_reward="مبلغ المكافأة اليومية الأساسي",
        invite_reward="مكافأة دعوة الأعضاء بالسيرفر الرئيسي",
        msg_reward_min="الحد الأدنى لمكافأة الرسائل",
        msg_reward_max="الحد الأقصى لمكافأة الرسائل",
        msg_enabled="تفعيل/تعطيل مكافآت الشات",
        voice_enabled="تفعيل/تعطيل مكافآت الرومات الصوتية",
        invite_enabled="تفعيل/تعطيل مكافآت الدعوات"
    )
    async def admin_settings(
        self,
        interaction: discord.Interaction,
        daily_reward: Optional[int] = None,
        invite_reward: Optional[int] = None,
        msg_reward_min: Optional[int] = None,
        msg_reward_max: Optional[int] = None,
        msg_enabled: Optional[bool] = None,
        voice_enabled: Optional[bool] = None,
        invite_enabled: Optional[bool] = None
    ):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            eco_service = EconomyService(session)
            if not await eco_service.perm_service.has_manager_permission(interaction.user, "ECONOMY_MANAGER"):
                await interaction.followup.send(embed=EmbedBuilder.error("عذراً", "ليس لديك صلاحية إدارة الاقتصاد (`ECONOMY_MANAGER`)!"), ephemeral=True)
                return

            kwargs = {}
            if daily_reward is not None: kwargs["daily_reward_amount"] = daily_reward
            if invite_reward is not None: kwargs["invite_reward_amount"] = invite_reward
            if msg_reward_min is not None: kwargs["message_reward_min"] = msg_reward_min
            if msg_reward_max is not None: kwargs["message_reward_max"] = msg_reward_max
            if msg_enabled is not None: kwargs["message_rewards_enabled"] = msg_enabled
            if voice_enabled is not None: kwargs["voice_rewards_enabled"] = voice_enabled
            if invite_enabled is not None: kwargs["invite_rewards_enabled"] = invite_enabled

            updated_es = await eco_service.eco_repo.update_economy_settings(interaction.guild.id, **kwargs)

            fields = [
                ("المكافأة اليومية", f"`{updated_es.daily_reward_amount}` سراب", True),
                ("مكافأة الدعوة", f"`{updated_es.invite_reward_amount}` سراب", True),
                ("نطاق مكافأة الرسائل", f"`{updated_es.message_reward_min} - {updated_es.message_reward_max}`", True),
                ("مكافآت الشات", "مفعلة ✅" if updated_es.message_rewards_enabled else "معطلة ❌", True),
                ("مكافآت الصوت", "مفعلة ✅" if updated_es.voice_rewards_enabled else "معطلة ❌", True),
                ("مكافآت الدعوات", "مفعلة ✅" if updated_es.invite_rewards_enabled else "معطلة ❌", True),
            ]

            embed = EmbedBuilder.success(
                title="تم تحديث إعدادات نظام الاقتصاد",
                description="تم حفظ التعديلات الجديدة بنجاح:",
                fields=fields
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


    # --- ALIAS COMMANDS FOR EASE OF USE ---

    @app_commands.command(name="cash", description="عرض رصيدك الحالي في المحفظة والبنك")
    @app_commands.describe(user="العضو المراد استعلام رصيده (اختياري)")
    async def cash_command(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        await self.balance_command.callback(self, interaction, user)

    @app_commands.command(name="رصيدي", description="عرض رصيدك الحالي في المحفظة والبنك")
    @app_commands.describe(user="العضو المراد استعلام رصيده (اختياري)")
    async def arabic_balance_command(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        await self.balance_command.callback(self, interaction, user)

    @app_commands.command(name="top", description="عرض لائحة أغنى الأعضاء في الاقتصاد")
    async def top_command(self, interaction: discord.Interaction):
        await self.leaderboard_command.callback(self, interaction)

    @app_commands.command(name="اغنياء", description="عرض لائحة أغنى الأعضاء في جميع السيرفرات")
    async def arabic_top_command(self, interaction: discord.Interaction):
        await self.leaderboard_command.callback(self, interaction)

async def setup(bot: commands.Bot):

    await bot.add_cog(EconomyCog(bot))
