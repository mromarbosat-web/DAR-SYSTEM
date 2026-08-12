import logging
import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.security_service import SecurityService
from bot.services.log_service import LogService
from bot.utils.embeds import EmbedBuilder
from bot.utils.audit_logs import format_mention, format_id
from bot.utils.time import utc_now

logger = logging.getLogger("discord_bot.events.member_join")

def register_member_join_event(bot: commands.Bot):
    @bot.event
    async def on_member_join(member: discord.Member):
        guild = member.guild
        async with AsyncSessionLocal() as session:
            # 1. Anti-Raid Processing
            sec_service = SecurityService(session)
            await sec_service.handle_member_join(member)

            # 2. Invite Tracking
            invite_info = None
            if not member.bot and hasattr(bot, "invite_tracker"):
                invite_info = await bot.invite_tracker.fetch_inviter(member)
                
                # referral rewards if main guild
                from bot.config.settings import settings
                if invite_info and invite_info != "vanity" and invite_info.inviter and guild.id == settings.MAIN_GUILD_ID:
                    from bot.services.economy_service import EconomyService
                    eco_service = EconomyService(session)
                    await eco_service.process_invite_reward(guild, invite_info.inviter.id, member)

            # 3. Member Join Log
            log_service = LogService(session)
            
            created_at = member.created_at
            account_age_str = f"<t:{int(created_at.timestamp())}:F> (<t:{int(created_at.timestamp())}:R>)"
            join_time_str = f"<t:{int(utc_now().timestamp())}:F>"
            
            fields = [
                ("👤 العضو", member.mention, True),
                ("🏷️ اسم المستخدم", f"`{member.name}`", True),
                ("📛 الاسم المستعار", f"`{member.display_name}`", True),
                ("🆔 معرف المستخدم", format_id(member.id), True),
                ("📅 إنشاء الحساب", account_age_str, False),
                ("📥 وقت الانضمام", join_time_str, True),
                ("👥 إجمالي الأعضاء", f"`{guild.member_count}`", True)
            ]
            
            invite_fields = []
            if invite_info:
                if invite_info == "vanity":
                    fields.append(("🔗 مصدر الدعوة", "`Vanity URL (رابط مخصص)`", False))
                    invite_fields.append(("🔗 مصدر الدعوة", "`Vanity URL (رابط مخصص)`", False))
                else:
                    inviter_str = f"{invite_info.inviter.mention} (`{invite_info.inviter.id}`)" if invite_info.inviter else "غير متاح"
                    fields.append(("📩 دعا بواسطة", inviter_str, False))
                    fields.append(("🎫 كود الدعوة", f"`{invite_info.code}`", True))
                    fields.append(("📈 الاستخدامات", f"`{invite_info.uses}`", True))
                    
                    invite_fields.extend([
                        ("👤 العضو المنضم", member.mention, True),
                        ("🆔 المعرف", format_id(member.id), True),
                        ("📩 الداعي", inviter_str, False),
                        ("🎫 الكود", f"`{invite_info.code}`", True),
                        ("📈 الاستخدامات", f"`{invite_info.uses}`", True)
                    ])

            embed = EmbedBuilder.log(
                title="🟢 انضمام عضو جديد",
                color=discord.Color.green(),
                fields=fields,
                author=member
            )
            await log_service.log_event(guild, "member", embed)
            
            if invite_fields:
                inv_embed = EmbedBuilder.log(
                    title="🔗 تتبع دعوة جديدة",
                    color=discord.Color.blue(),
                    fields=invite_fields,
                    author=member
                )
                await log_service.log_event(guild, "invite", inv_embed)

