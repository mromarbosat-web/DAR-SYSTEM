import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.audit_logs import get_audit_log_executor, format_mention, format_id
from bot.utils.embeds import EmbedBuilder
from bot.utils.time import utc_now

def register_role_logs_events(bot: commands.Bot):
    @bot.event
    async def on_guild_role_create(role: discord.Role):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            fields = [
                ("🛡️ الرتبة", role.mention, True),
                ("🏷️ الاسم", f"`{role.name}`", True),
                ("🆔 المعرف", format_id(role.id), True),
                ("🎨 اللون", f"`{role.color}`", True),
                ("📊 الترتيب", f"`{role.position}`", True)
            ]
            
            executor = await get_audit_log_executor(role.guild, discord.AuditLogAction.role_create, role.id)
            if executor:
                fields.append(("👮 أنشئت بواسطة", executor.mention, False))

            embed = EmbedBuilder.log(
                title="🛡️ تم إنشاء رتبة جديدة",
                color=discord.Color.green(),
                fields=fields
            )
            await log_service.log_event(role.guild, "role", embed)

    @bot.event
    async def on_guild_role_delete(role: discord.Role):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            # Since role is already deleted, mention won't work perfectly if not in cache
            fields = [
                ("🛡️ الرتبة", f"`{role.name}`", True),
                ("🆔 المعرف", format_id(role.id), True),
                ("🎨 اللون", f"`{role.color}`", True),
                ("📊 الترتيب", f"`{role.position}`", True)
            ]
            
            executor = await get_audit_log_executor(role.guild, discord.AuditLogAction.role_delete, role.id)
            if executor:
                fields.append(("👮 حذفت بواسطة", executor.mention, False))

            embed = EmbedBuilder.log(
                title="🗑️ تم حذف رتبة",
                color=discord.Color.red(),
                fields=fields
            )
            await log_service.log_event(role.guild, "role", embed)

    @bot.event
    async def on_guild_role_update(before: discord.Role, after: discord.Role):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            changes = []
            if before.name != after.name:
                changes.append(f"🔹 **الاسم:** `{before.name}` ➔ `{after.name}`")
            if before.color != after.color:
                changes.append(f"🔹 **اللون:** `{before.color}` ➔ `{after.color}`")
            if before.hoist != after.hoist:
                val = "نعم" if after.hoist else "لا"
                changes.append(f"🔹 **عرض منفصل:** `{val}`")
            if before.mentionable != after.mentionable:
                val = "نعم" if after.mentionable else "لا"
                changes.append(f"🔹 **قابلة للمنشن:** `{val}`")
            if before.permissions != after.permissions:
                changes.append("🔹 **تعديل الصلاحيات (Permissions)**")
            if before.position != after.position:
                changes.append(f"🔹 **الترتيب:** `{before.position}` ➔ `{after.position}`")
                
            if not changes:
                return

            fields = [
                ("🛡️ الرتبة", after.mention, True),
                ("🆔 المعرف", format_id(after.id), True),
                ("📝 التغييرات", "\n".join(changes), False)
            ]
            
            executor = await get_audit_log_executor(after.guild, discord.AuditLogAction.role_update, after.id)
            if executor:
                fields.append(("👮 عدلت بواسطة", executor.mention, False))

            embed = EmbedBuilder.log(
                title="🛡️ تم تعديل رتبة",
                color=discord.Color.gold(),
                fields=fields
            )
            await log_service.log_event(after.guild, "role", embed)

