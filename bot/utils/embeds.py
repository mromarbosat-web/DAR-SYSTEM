import discord
from typing import Optional, List
from bot.config.settings import settings

class EmbedBuilder:
    @staticmethod
    def success(title: str, description: str, fields: Optional[List[tuple]] = None) -> discord.Embed:
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=settings.COLOR_SUCCESS
        )
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        embed.set_footer(text="Security & Management Bot • النظام الأمني الإداري")
        return embed

    @staticmethod
    def error(title: str, description: str, fields: Optional[List[tuple]] = None) -> discord.Embed:
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=settings.COLOR_ERROR
        )
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        embed.set_footer(text="Security & Management Bot • النظام الأمني الإداري")
        return embed

    @staticmethod
    def warning(title: str, description: str, fields: Optional[List[tuple]] = None) -> discord.Embed:
        embed = discord.Embed(
            title=f"⚠️ {title}",
            description=description,
            color=settings.COLOR_WARNING
        )
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        embed.set_footer(text="Security & Management Bot • النظام الأمني الإداري")
        return embed

    @staticmethod
    def info(title: str, description: str, fields: Optional[List[tuple]] = None) -> discord.Embed:
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=description,
            color=settings.COLOR_INFO
        )
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        embed.set_footer(text="Security & Management Bot • النظام الأمني الإداري")
        return embed

    @staticmethod
    def security_alert(title: str, description: str, fields: Optional[List[tuple]] = None) -> discord.Embed:
        embed = discord.Embed(
            title=f"🛡️ تنبيه أمني خطير - {title}",
            description=description,
            color=settings.COLOR_SECURITY
        )
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        embed.set_footer(text="Security & Management System • Anti-Raid & Anti-Nuke")
        return embed
