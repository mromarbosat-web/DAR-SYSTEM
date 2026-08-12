import re

with open('bot/cogs/economy.py', 'r') as f:
    content = f.read()

aliases_code = """
    # --- ALIAS COMMANDS FOR EASE OF USE ---

    @app_commands.command(name="cash", description="عرض رصيدك الحالي في المحفظة والبنك")
    @app_commands.describe(user="العضو المراد استعلام رصيده (اختياري)")
    async def cash_command(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        await self.balance_command.callback(self, interaction, user)

    @app_commands.command(name="رصيدي", description="عرض رصيدك الحالي في المحفظة والبنك")
    @app_commands.describe(user="العضو المراد استعلام رصيده (اختياري)")
    async def arabic_balance_command(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        await self.balance_command.callback(self, interaction, user)

    @app_commands.command(name="top", description="عرض لائحة أغنى الأعضاء في الاقتصاد")
    async def top_command(self, interaction: discord.Interaction):
        await self.leaderboard_command.callback(self, interaction)

    @app_commands.command(name="اغنياء", description="عرض لائحة أغنى الأعضاء في جميع السيرفرات")
    async def arabic_top_command(self, interaction: discord.Interaction):
        await self.leaderboard_command.callback(self, interaction)

    @app_commands.command(name="يومي", description="المطالبة بالمكافأة اليومية")
    async def arabic_daily_command(self, interaction: discord.Interaction):
        await self.daily_command.callback(self, interaction)

async def setup(bot: commands.Bot):
"""

content = content.replace("async def setup(bot: commands.Bot):", aliases_code)

with open('bot/cogs/economy.py', 'w') as f:
    f.write(content)
