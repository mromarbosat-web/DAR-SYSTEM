import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.embeds import EmbedBuilder

class UtilityCog(commands.Cog):
    """Cog for Bot Info, Ping, and Server Utility commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="فحص سرعة استجابة وتأخير البوت (Latency)")
    async def ping_command(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = EmbedBuilder.info(
            title="سرعة الاستجابة (Bot Latency)",
            description=f"🏓 Pong! زَمَن الاستجابة الحالي: **{latency}ms**"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="معلومات تقنية شاملة عن البوت وحالته")
    async def botinfo_command(self, interaction: discord.Interaction):
        guilds_count = len(self.bot.guilds)
        total_users = sum(g.member_count or 0 for g in self.bot.guilds)
        latency = round(self.bot.latency * 1000)

        fields = [
            ("السيرفرات المربوطة", f"`{guilds_count}` سيرفر", True),
            ("إجمالي الأعضاء", f"`{total_users}` عضو", True),
            ("زَمَن الاستجابة", f"`{latency}ms`", True),
            ("التقنية واستضافة الإنتاج", "Python `discord.py` • Supabase PostgreSQL • Railway Worker", False)
        ]

        embed = EmbedBuilder.info(
            title="Security & Management Bot",
            description="بوت حماية وإدارة السيرفرات الاحترافي متوافق كليًا مع أحدث بروتوكولات Discord Slash Commands.",
            fields=fields
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))
