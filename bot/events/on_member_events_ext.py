import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.audit_logs import get_audit_log_executor, format_mention, format_id
from bot.utils.embeds import EmbedBuilder

def register_member_logs_ext_events(bot: commands.Bot):
    @bot.event
    async def on_member_update(before: discord.Member, after: discord.Member):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            # Nickname Change
            if before.nick != after.nick:
                b_nick = before.nick if before.nick else "بدون اسم مستعار"
                a_nick = after.nick if after.nick else "تمت الإزالة"
                fields = [
                    ("👤 العضو", after.mention, True),
                    ("🆔 المعرف", format_id(after.id), True),
                    ("📝 قبل", f"`{b_nick}`", True),
                    ("📝 بعد", f"`{a_nick}`", True)
                ]
                
                executor = await get_audit_log_executor(after.guild, discord.AuditLogAction.member_update, after.id)
                if executor:
                    fields.append(("👮 بواسطة", executor.mention, False))

                embed = EmbedBuilder.log(
                    title="👤 تغيير الاسم المستعار (Nickname)",
                    color=discord.Color.blue(),
                    fields=fields,
                    author=after
                )
                await log_service.log_event(after.guild, "member", embed)
                
            # Role Change
            if before.roles != after.roles:
                added_roles = [r for r in after.roles if r not in before.roles]
                removed_roles = [r for r in before.roles if r not in after.roles]
                
                if added_roles or removed_roles:
                    fields = [
                        ("👤 العضو", after.mention, True),
                        ("🆔 المعرف", format_id(after.id), True)
                    ]
                    if added_roles:
                        fields.append(("✅ الرتب المضافة", " ".join([r.mention for r in added_roles]), False))
                    if removed_roles:
                        fields.append(("❌ الرتب المزالة", " ".join([r.mention for r in removed_roles]), False))
                    
                    executor = await get_audit_log_executor(after.guild, discord.AuditLogAction.member_role_update, after.id)
                    if executor:
                        fields.append(("👮 بواسطة", executor.mention, False))

                    embed = EmbedBuilder.log(
                        title="🛡️ تحديث رتب العضو",
                        color=discord.Color.gold(),
                        fields=fields,
                        author=after
                    )
                    await log_service.log_event(after.guild, "member", embed)

            # Timeout check
            if before.timed_out_until != after.timed_out_until:
                if after.timed_out_until:
                    title = "⏳ تم إسكات عضو (Timeout)"
                    until = f"<t:{int(after.timed_out_until.timestamp())}:F> (<t:{int(after.timed_out_until.timestamp())}:R>)"
                    fields = [
                        ("👤 المستهدف", after.mention, True),
                        ("🆔 المعرف", format_id(after.id), True),
                        ("⏰ ينتهي في", until, False)
                    ]
                    
                    executor = await get_audit_log_executor(after.guild, discord.AuditLogAction.member_update, after.id)
                    if executor:
                        fields.append(("👮 المنفذ", executor.mention, True))
                        
                    embed = EmbedBuilder.log(title=title, color=discord.Color.dark_orange(), fields=fields, author=after)
                    await log_service.log_event(after.guild, "moderation", embed)
                else:
                    title = "🔊 تمت إزالة الإسكات (Timeout Removed)"
                    fields = [
                        ("👤 المستهدف", after.mention, True),
                        ("🆔 المعرف", format_id(after.id), True)
                    ]
                    executor = await get_audit_log_executor(after.guild, discord.AuditLogAction.member_update, after.id)
                    if executor:
                        fields.append(("👮 المنفذ", executor.mention, True))
                    embed = EmbedBuilder.log(title=title, color=discord.Color.green(), fields=fields, author=after)
                    await log_service.log_event(after.guild, "moderation", embed)

    @bot.event
    async def on_user_update(before: discord.User, after: discord.User):
        for guild in bot.guilds:
            if guild.get_member(after.id):
                async with AsyncSessionLocal() as session:
                    log_service = LogService(session)
                    if before.name != after.name:
                        fields = [
                            ("👤 المستخدم", after.mention, True),
                            ("📝 قبل", f"`{before.name}`", True),
                            ("📝 بعد", f"`{after.name}`", True)
                        ]
                        embed = EmbedBuilder.log(title="👤 تغيير اسم الحساب", color=discord.Color.blue(), fields=fields, author=after)
                        await log_service.log_event(guild, "member", embed)
                        
                    if before.avatar != after.avatar:
                        fields = [
                            ("👤 المستخدم", after.mention, True)
                        ]
                        embed = EmbedBuilder.log(title="👤 تغيير الصورة الشخصية", color=discord.Color.blue(), fields=fields, author=after)
                        if after.avatar:
                            embed.set_thumbnail(url=after.avatar.url)
                        await log_service.log_event(guild, "member", embed)

    @bot.event
    async def on_member_ban(guild: discord.Guild, user: discord.User):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            fields = [
                ("👤 المحظور", user.mention, True),
                ("🆔 المعرف", format_id(user.id), True)
            ]
            
            executor = await get_audit_log_executor(guild, discord.AuditLogAction.ban, user.id)
            if executor:
                fields.append(("👮 المنفذ", executor.mention, True))
                # Try to find reason if not found in executor (unlikely in audit log)
                async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
                    if entry.target.id == user.id and entry.reason:
                        fields.append(("📝 السبب", f"`{entry.reason}`", False))
                        break

            embed = EmbedBuilder.log(
                title="🔨 تم حظر عضو (Ban)",
                color=discord.Color.dark_red(),
                fields=fields,
                author=user
            )
            await log_service.log_event(guild, "moderation", embed)

    @bot.event
    async def on_member_unban(guild: discord.Guild, user: discord.User):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            fields = [
                ("👤 المستخدم", user.mention, True),
                ("🆔 المعرف", format_id(user.id), True)
            ]
            
            executor = await get_audit_log_executor(guild, discord.AuditLogAction.unban, user.id)
            if executor:
                fields.append(("👮 المنفذ", executor.mention, True))

            embed = EmbedBuilder.log(
                title="🔓 تم فك الحظر (Unban)",
                color=discord.Color.green(),
                fields=fields,
                author=user
            )
            await log_service.log_event(guild, "moderation", embed)
