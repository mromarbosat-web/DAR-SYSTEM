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

    @staticmethod
    def log(title: str, color: discord.Color = settings.COLOR_INFO, fields: Optional[List[tuple]] = None, author: Optional[discord.Member] = None, footer: Optional[str] = None) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=discord.utils.utcnow()
        )
        if author:
            embed.set_author(name=f"{author} ({author.id})", icon_url=author.display_avatar.url if author.display_avatar else None)
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        
        footer_text = footer if footer else "نظام السجلات واللوجز • Security & Management"
        embed.set_footer(text=footer_text)
        return embed
