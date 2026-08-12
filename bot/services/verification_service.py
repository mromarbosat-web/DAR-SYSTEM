import logging
import discord
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.repositories.verification_repository import VerificationRepository
from bot.services.log_service import LogService
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.verification_service")

class VerificationView(discord.ui.View):
    def __init__(self, session_factory):
        super().__init__(timeout=None) # Persistent view
        self.session_factory = session_factory

    @discord.ui.button(
        label="تحقق الآن / Verify",
        style=discord.ButtonStyle.green,
        custom_id="verification_button_persistent",
        emoji="🔐"
    )
    async def verify_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        user = interaction.user

        if not guild or not isinstance(user, discord.Member):
            await interaction.followup.send("❌ هذا الإجراء متاح داخل السيرفرات فقط.", ephemeral=True)
            return

        async with self.session_factory() as session:
            verif_repo = VerificationRepository(session)
            log_service = LogService(session)

            verif = await verif_repo.get_verification_settings(guild.id)
            if not verif or not verif.enabled:
                await interaction.followup.send("⚠️ نظام التحقق غير مفعّل حاليًا في هذا السيرفر.", ephemeral=True)
                return

            if not verif.verified_role_id:
                await interaction.followup.send("⚠️ لم يتم تحديد رتبة التحقق (Verified Role) من قبل إداري السيرفر.", ephemeral=True)
                return

            verified_role = guild.get_role(verif.verified_role_id)
            if not verified_role:
                await interaction.followup.send("❌ تعذر العثور على رتبة التحقق في السيرفر.", ephemeral=True)
                return

            # Check if user is already verified
            if verified_role in user.roles:
                await interaction.followup.send("ℹ️ أنت موثق بالفعل وممتلك لرتبة التحقق!", ephemeral=True)
                return

            # Grant Verified Role & Remove Unverified Role
            try:
                roles_to_add = [verified_role]
                roles_to_remove = []

                if verif.unverified_role_id:
                    unverif_role = guild.get_role(verif.unverified_role_id)
                    if unverif_role and unverif_role in user.roles:
                        roles_to_remove.append(unverif_role)

                await user.add_roles(*roles_to_add, reason="Verification Completed")
                if roles_to_remove:
                    await user.remove_roles(*roles_to_remove, reason="Verification Completed")

                await interaction.followup.send("✅ **تم التحقق بنجاح!** تمت إضافتك إلى أعضاء السيرفر الموثقين.", ephemeral=True)

                # Send Log
                log_embed = EmbedBuilder.success(
                    title="عملية تحقق ناجحة (Member Verified)",
                    description=f"أكمل العضو {user.mention} عملية التحقق بنجاح.",
                    fields=[
                        ("العضو", f"{user} (`{user.id}`)", True),
                        ("الرتبة الممنوحة", verified_role.mention, True)
                    ]
                )
                await log_service.log_event(guild, "member", log_embed)

            except discord.Forbidden:
                await interaction.followup.send("❌ خطأ: لا يملك البوت الصلاحيات الكافية لإعطاء الرتبة (تأكد من وضع رتبة البوت أعلى من رتبة التحقق).", ephemeral=True)
            except Exception as e:
                logger.error(f"Error verifying user {user.id} in guild {guild.id}: {e}")
                await interaction.followup.send("❌ حدث خطأ غير متوقع أثناء إكمال التحقق.", ephemeral=True)

class VerificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.verif_repo = VerificationRepository(session)

    async def setup_panel(
        self,
        guild: discord.Guild,
        channel: discord.TextChannel,
        verified_role: discord.Role,
        unverified_role: Optional[discord.Role] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        session_factory = None
    ) -> discord.Message:
        """Creates or updates the Verification Panel message in the specified channel"""
        verif = await self.verif_repo.update_verification_settings(
            guild_id=guild.id,
            enabled=True,
            channel_id=channel.id,
            verified_role_id=verified_role.id,
            unverified_role_id=unverified_role.id if unverified_role else None,
            title=title or "نظام التحقق - Verification System",
            description=description or "اضغط على الزر أدناه لإكمال عملية التحقق والحصول على الرتبة."
        )

        embed = EmbedBuilder.info(
            title=verif.title,
            description=f"{verif.description}\n\n🔒 **Verified Role:** {verified_role.mention}"
        )

        view = VerificationView(session_factory)
        msg = await channel.send(embed=embed, view=view)

        await self.verif_repo.update_verification_settings(
            guild_id=guild.id,
            panel_message_id=msg.id
        )

        return msg
