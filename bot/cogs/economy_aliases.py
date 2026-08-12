import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from bot.cogs.economy import EconomyCog

class EconomyAliasesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.eco_cog = bot.get_cog("EconomyCog")

    @app_commands.command(name="cash", description="عرض رصيدك الحالي في المحفظة والبنك")
    @app_commands.describe(user="العضو المراد استعلام رصيده (اختياري)")
    async def cash_command(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        if not self.eco_cog:
            self.eco_cog = self.bot.get_cog("EconomyCog")
        await self.eco_cog.balance_command.callback(self.eco_cog, interaction, user)

    @app_commands.command(name="رصيد", description="عرض رصيدك الحالي في المحفظة والبنك")
    @app_commands.describe(user="العضو المراد استعلام رصيده (اختياري)")
    async def arabic_balance_command(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        if not self.eco_cog:
            self.eco_cog = self.bot.get_cog("EconomyCog")
        await self.eco_cog.balance_command.callback(self.eco_cog, interaction, user)

    @app_commands.command(name="top", description="عرض لائحة أغنى الأعضاء في الاقتصاد")
    async def top_command(self, interaction: discord.Interaction):
        if not self.eco_cog:
            self.eco_cog = self.bot.get_cog("EconomyCog")
        await self.eco_cog.leaderboard_command.callback(self.eco_cog, interaction)

    @app_commands.command(name="توب", description="عرض لائحة أغنى الأعضاء في جميع السيرفرات")
    async def arabic_top_command(self, interaction: discord.Interaction):
        if not self.eco_cog:
            self.eco_cog = self.bot.get_cog("EconomyCog")
        await self.eco_cog.leaderboard_command.callback(self.eco_cog, interaction)

async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyAliasesCog(bot))
