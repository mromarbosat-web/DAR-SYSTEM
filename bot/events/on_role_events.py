import discord
from discord.ext import commands
from bot.database.connection import AsyncSessionLocal
from bot.services.log_service import LogService
from bot.utils.time import utc_now

def register_role_logs_events(bot: commands.Bot):
    @bot.event
    async def on_guild_role_create(role: discord.Role):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            embed = discord.Embed(title="🛡️ Role Created", color=discord.Color.green(), timestamp=utc_now())
            embed.add_field(name="Role", value=f"{role.mention} (`{role.name}`)", inline=False)
            embed.set_footer(text=f"Role ID: {role.id}")
            await log_service.log_event(role.guild, "role", embed)

    @bot.event
    async def on_guild_role_delete(role: discord.Role):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            embed = discord.Embed(title="🛡️ Role Deleted", color=discord.Color.red(), timestamp=utc_now())
            embed.add_field(name="Role", value=f"`{role.name}`", inline=False)
            embed.set_footer(text=f"Role ID: {role.id}")
            await log_service.log_event(role.guild, "role", embed)

    @bot.event
    async def on_guild_role_update(before: discord.Role, after: discord.Role):
        async with AsyncSessionLocal() as session:
            log_service = LogService(session)
            
            changes = []
            if before.name != after.name:
                changes.append(f"**Name:** `{before.name}` ➔ `{after.name}`")
            if before.color != after.color:
                changes.append(f"**Color:** `{before.color}` ➔ `{after.color}`")
            if before.hoist != after.hoist:
                changes.append(f"**Displayed separately:** `{before.hoist}` ➔ `{after.hoist}`")
            if before.mentionable != after.mentionable:
                changes.append(f"**Mentionable:** `{before.mentionable}` ➔ `{after.mentionable}`")
                
            if not changes and before.permissions != after.permissions:
                changes.append("**Permissions updated** (See Audit Log for details)")
                
            if changes:
                embed = discord.Embed(title="🛡️ Role Updated", description="\n".join(changes), color=discord.Color.gold(), timestamp=utc_now())
                embed.add_field(name="Role", value=f"{after.mention} (`{after.name}`)", inline=False)
                embed.set_footer(text=f"Role ID: {after.id}")
                await log_service.log_event(after.guild, "role", embed)

