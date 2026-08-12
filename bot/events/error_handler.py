import logging
import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.events.errors")

def register_error_handlers(bot: commands.Bot):
    
    # Global Slash Command Tree Error Handler
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        # Unwrap command invoke errors
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if isinstance(error, app_commands.MissingPermissions):
            missing = ", ".join(f"`{perm}`" for perm in error.missing_permissions)
            embed = EmbedBuilder.error(
                title="صلاحيات غير كافية (Missing Permissions)",
                description=f"أنت لا تمتلك الصلاحيات الإدارية الكافية لتنفيذ هذا الأمر!\n**الصلاحيات المطلوبة:** {missing}"
            )
        elif isinstance(error, app_commands.BotMissingPermissions):
            missing = ", ".join(f"`{perm}`" for perm in error.missing_permissions)
            embed = EmbedBuilder.error(
                title="صلاحيات البوت غير كافية (Bot Missing Permissions)",
                description=f"لا يمتلك البوت الصلاحيات اللازمة للتنفيذ!\n**الصلاحيات المفقودة:** {missing}"
            )
        elif isinstance(error, app_commands.CommandOnCooldown):
            embed = EmbedBuilder.warning(
                title="الأمر قيد التبريد (Cooldown)",
                description=f"يرجى الانتظار `{error.retry_after:.1f}` ثانية قبل إعادة استخدام هذا الأمر."
            )
        else:
            logger.error(f"Unhandled app command error in /{interaction.command.name if interaction.command else 'unknown'}: {error}", exc_info=True)
            embed = EmbedBuilder.error(
                title="حدث خطأ أثناء تنفيذ الأمر",
                description="وقع خطأ غَيْر متوقع أثناء معالجة الأمر. تم تسجيل الخطأ في السجلات الإدارية للمراجعة."
            )

        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to send error embed response: {e}")

    bot.tree.on_error = on_app_command_error

    @bot.event
    async def on_command_error(ctx: commands.Context, error: commands.CommandError):
        """Prefix Command Error Handler"""
        if isinstance(error, commands.CommandNotFound):
            return # Ignore invalid prefix commands
            
        logger.error(f"Prefix command error in {ctx.command}: {error}")
