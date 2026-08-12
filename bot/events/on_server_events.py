import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.audit_logs import get_audit_log_executor, format_mention, format_id
from bot.utils.embeds import EmbedBuilder

def register_server_logs_events(bot: commands.Bot):
    @bot.event
    async def on_guild_update(before: discord.Guild, after: discord.Guild):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            fields = []
            if before.name != after.name:
                fields.append(("📝 الاسم السابق", f"`{before.name}`", True))
                fields.append(("📝 الاسم الجديد", f"`{after.name}`", True))
            if before.verification_level != after.verification_level:
                fields.append(("🛡️ مستوى التحقق السابق", f"`{before.verification_level.name}`", True))
                fields.append(("🛡️ مستوى التحقق الجديد", f"`{after.verification_level.name}`", True))
            if before.vanity_url_code != after.vanity_url_code:
                v_before = before.vanity_url_code if before.vanity_url_code else "لا يوجد"
                v_after = after.vanity_url_code if after.vanity_url_code else "لا يوجد"
                fields.append(("🔗 الرابط المخصص السابق", f"`{v_before}`", True))
                fields.append(("🔗 الرابط المخصص الجديد", f"`{v_after}`", True))
            
            if fields:
                executor = await get_audit_log_executor(after, discord.AuditLogAction.guild_update)
                if executor:
                    fields.append(("👮 المنفذ", executor.mention, False))

                embed = EmbedBuilder.log(
                    title="⚙️ تحديث إعدادات السيرفر",
                    color=discord.Color.purple(),
                    fields=fields,
                    author=after
                )
                embed.set_thumbnail(url=after.icon.url if after.icon else None)
                await log_service.log_event(after, "server", embed)
                
            if before.icon != after.icon:
                fields = []
                if before.icon:
                    fields.append(("🖼️ الأيقونة السابقة", f"[رابط]({before.icon.url})", True))
                
                executor = await get_audit_log_executor(after, discord.AuditLogAction.guild_update)
                if executor:
                    fields.append(("👮 المنفذ", executor.mention, False))

                embed = EmbedBuilder.log(
                    title="🖼️ تحديث أيقونة السيرفر",
                    color=discord.Color.purple(),
                    fields=fields,
                    author=after
                )
                if after.icon:
                    embed.set_thumbnail(url=after.icon.url)
                await log_service.log_event(after, "server", embed)

            if before.banner != after.banner:
                fields = []
                if before.banner:
                    fields.append(("🖼️ البانر السابق", f"[رابط]({before.banner.url})", True))
                
                executor = await get_audit_log_executor(after, discord.AuditLogAction.guild_update)
                if executor:
                    fields.append(("👮 المنفذ", executor.mention, False))

                embed = EmbedBuilder.log(
                    title="🖼️ تحديث بانر السيرفر",
                    color=discord.Color.purple(),
                    fields=fields,
                    author=after
                )
                if after.banner:
                    embed.set_image(url=after.banner.url)
                await log_service.log_event(after, "server", embed)

    @bot.event
    async def on_invite_create(invite: discord.Invite):
        if hasattr(bot, "invites_cache") and invite.guild.id in bot.invites_cache:
            bot.invites_cache[invite.guild.id][invite.code] = invite.uses
            
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            fields = [
                ("📝 الكود", f"`{invite.code}`", True),
                ("📺 القناة", invite.channel.mention, True)
            ]
            if invite.inviter:
                fields.append(("👮 المنشئ", invite.inviter.mention, True))
            
            if invite.max_uses > 0:
                fields.append(("📊 أقصى استخدام", f"`{invite.max_uses}`", True))
            else:
                fields.append(("📊 أقصى استخدام", "∞", True))
                
            if invite.max_age > 0:
                from bot.utils.time import utc_now
                import datetime
                expires = utc_now() + datetime.timedelta(seconds=invite.max_age)
                fields.append(("⏰ ينتهي في", f"<t:{int(expires.timestamp())}:R>", True))
            else:
                fields.append(("⏰ ينتهي في", "لا ينتهي", True))

            embed = EmbedBuilder.log(
                title="🔗 إنشاء رابط دعوة جديد",
                color=discord.Color.green(),
                fields=fields,
                author=invite.inviter if invite.inviter else invite.guild
            )
            await log_service.log_event(invite.guild, "server", embed)

    @bot.event
    async def on_invite_delete(invite: discord.Invite):
        if hasattr(bot, "invites_cache") and invite.guild.id in bot.invites_cache:
            if invite.code in bot.invites_cache[invite.guild.id]:
                del bot.invites_cache[invite.guild.id][invite.code]
                
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            fields = [
                ("📝 الكود", f"`{invite.code}`", True),
                ("📺 القناة", format_mention(invite.channel), True)
            ]
            
            executor = await get_audit_log_executor(invite.guild, discord.AuditLogAction.invite_delete)
            if executor:
                fields.append(("👮 حذف بواسطة", executor.mention, False))

            embed = EmbedBuilder.log(
                title="🔗 حذف رابط دعوة",
                color=discord.Color.red(),
                fields=fields,
                author=executor if executor else invite.guild
            )
            await log_service.log_event(invite.guild, "server", embed)

