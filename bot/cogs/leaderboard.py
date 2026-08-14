import logging
from typing import Optional
import discord
from discord import app_commands, ui
from discord.ext import commands

from bot.database.connection import AsyncSessionLocal
from bot.services.activity_service import ActivityService
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.cogs.leaderboard")

class LeaderboardView(ui.View):
    """
    Interactive View for dynamically switching between Text & Voice leaderboards
    as well as Daily, Weekly, Monthly, and All-Time intervals.
    """
    def __init__(
        self,
        guild: discord.Guild,
        current_type: str = "text",
        current_period: str = "daily",
        requester_id: Optional[int] = None
    ):
        super().__init__(timeout=180)
        self.guild = guild
        self.current_type = current_type # "text" or "voice"
        self.current_period = current_period # "daily", "weekly", "monthly", "all_time"
        self.requester_id = requester_id
        self._update_button_states()

    def _update_button_states(self):
        # Type buttons
        self.btn_text.style = discord.ButtonStyle.primary if self.current_type == "text" else discord.ButtonStyle.secondary
        self.btn_voice.style = discord.ButtonStyle.success if self.current_type == "voice" else discord.ButtonStyle.secondary
        
        # Period buttons
        self.btn_daily.style = discord.ButtonStyle.primary if self.current_period == "daily" else discord.ButtonStyle.secondary
        self.btn_weekly.style = discord.ButtonStyle.primary if self.current_period == "weekly" else discord.ButtonStyle.secondary
        self.btn_monthly.style = discord.ButtonStyle.primary if self.current_period == "monthly" else discord.ButtonStyle.secondary
        self.btn_all_time.style = discord.ButtonStyle.primary if self.current_period == "all_time" else discord.ButtonStyle.secondary

    async def _update_view(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self._update_button_states()
        async with AsyncSessionLocal() as session:
            service = ActivityService(session)
            embed, file = await service.build_leaderboard(
                guild=self.guild,
                activity_type=self.current_type,
                period=self.current_period
            )
            attachments = [file] if file else []
            await interaction.edit_original_response(embed=embed, attachments=attachments, view=self)

    @ui.button(label="💬 توب الكتابة", style=discord.ButtonStyle.primary, row=0, custom_id="btn_lb_text")
    async def btn_text(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_type != "text":
            self.current_type = "text"
            await self._update_view(interaction)
        else:
            await interaction.response.defer()

    @ui.button(label="🎙️ توب الفويس", style=discord.ButtonStyle.secondary, row=0, custom_id="btn_lb_voice")
    async def btn_voice(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_type != "voice":
            self.current_type = "voice"
            await self._update_view(interaction)
        else:
            await interaction.response.defer()

    @ui.button(label="📅 اليومي", style=discord.ButtonStyle.primary, row=1, custom_id="btn_lb_daily")
    async def btn_daily(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_period != "daily":
            self.current_period = "daily"
            await self._update_view(interaction)
        else:
            await interaction.response.defer()

    @ui.button(label="📆 الأسبوعي", style=discord.ButtonStyle.secondary, row=1, custom_id="btn_lb_weekly")
    async def btn_weekly(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_period != "weekly":
            self.current_period = "weekly"
            await self._update_view(interaction)
        else:
            await interaction.response.defer()

    @ui.button(label="🗓️ الشهري", style=discord.ButtonStyle.secondary, row=1, custom_id="btn_lb_monthly")
    async def btn_monthly(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_period != "monthly":
            self.current_period = "monthly"
            await self._update_view(interaction)
        else:
            await interaction.response.defer()

    @ui.button(label="🌐 الكلي", style=discord.ButtonStyle.secondary, row=1, custom_id="btn_lb_all")
    async def btn_all_time(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_period != "all_time":
            self.current_period = "all_time"
            await self._update_view(interaction)
        else:
            await interaction.response.defer()

class LeaderboardCog(commands.Cog, name="لوحة المتصدرين"):
    """أوامر لوحة الشرف وإحصائيات المتصدرين في الكتابة والرومات الصوتية."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="top", description="عرض لوحة شرف المتصدرين في الكتابة أو الفويس (يومي، أسبوعي، شهري، كلي)")
    @app_commands.describe(
        activity_type="نوع النشاط (كتابة رسائل أو رومات صوتية)",
        period="الفترة الزمنية للإحصائيات"
    )
    @app_commands.choices(
        activity_type=[
            app_commands.Choice(name="💬 الكتابة والرسائل (Text)", value="text"),
            app_commands.Choice(name="🎙️ الرومات الصوتية (Voice)", value="voice"),
        ],
        period=[
            app_commands.Choice(name="📅 اليومي (Daily)", value="daily"),
            app_commands.Choice(name="📆 الأسبوعي (Weekly)", value="weekly"),
            app_commands.Choice(name="🗓️ الشهري (Monthly)", value="monthly"),
            app_commands.Choice(name="🌐 الكلي (All-Time)", value="all_time"),
        ]
    )
    async def top_slash(
        self,
        interaction: discord.Interaction,
        activity_type: Optional[app_commands.Choice[str]] = None,
        period: Optional[app_commands.Choice[str]] = None
    ):
        if not interaction.guild:
            await interaction.response.send_message("❌ هذا الأمر متاح داخل السيرفرات فقط.", ephemeral=True)
            return

        await interaction.response.defer()
        
        act_type = activity_type.value if activity_type else "text"
        time_period = period.value if period else "daily"

        async with AsyncSessionLocal() as session:
            service = ActivityService(session)
            embed, file = await service.build_leaderboard(
                guild=interaction.guild,
                activity_type=act_type,
                period=time_period
            )

        view = LeaderboardView(
            guild=interaction.guild,
            current_type=act_type,
            current_period=time_period,
            requester_id=interaction.user.id
        )

        attachments = [file] if file else []
        await interaction.followup.send(embed=embed, files=attachments, view=view)

    @app_commands.command(name="توب", description="عرض لوحة شرف المتصدرين في الكتابة أو الفويس")
    @app_commands.describe(
        activity_type="نوع النشاط (كتابة رسائل أو رومات صوتية)",
        period="الفترة الزمنية للإحصائيات"
    )
    @app_commands.choices(
        activity_type=[
            app_commands.Choice(name="💬 الكتابة والرسائل (Text)", value="text"),
            app_commands.Choice(name="🎙️ الرومات الصوتية (Voice)", value="voice"),
        ],
        period=[
            app_commands.Choice(name="📅 اليومي (Daily)", value="daily"),
            app_commands.Choice(name="📆 الأسبوعي (Weekly)", value="weekly"),
            app_commands.Choice(name="🗓️ الشهري (Monthly)", value="monthly"),
            app_commands.Choice(name="🌐 الكلي (All-Time)", value="all_time"),
        ]
    )
    async def top_arabic_slash(
        self,
        interaction: discord.Interaction,
        activity_type: Optional[app_commands.Choice[str]] = None,
        period: Optional[app_commands.Choice[str]] = None
    ):
        await self.top_slash.callback(self, interaction, activity_type, period)

    @commands.command(name="top", aliases=["توب", "lb", "متصدرين", "المتصدرين", "toptext", "topvoice"])
    async def top_prefix(self, ctx: commands.Context, *args):
        """عرض لوحة شرف المتصدرين"""
        if not ctx.guild:
            return

        # Parse potential args e.g. !top voice weekly or !توب فويس اسبوع
        act_type = "text"
        time_period = "daily"

        args_str = " ".join(args).lower()
        if any(w in args_str for w in ["voice", "فويس", "صوت", "رومات", "صوتي"]):
            act_type = "voice"
        elif any(w in args_str for w in ["text", "كتابة", "رسائل", "شات", "رساله"]):
            act_type = "text"

        if any(w in args_str for w in ["week", "weekly", "اسبوع", "أسبوع", "اسبوعي", "أسبوعي"]):
            time_period = "weekly"
        elif any(w in args_str for w in ["month", "monthly", "شهر", "شهري"]):
            time_period = "monthly"
        elif any(w in args_str for w in ["all", "alltime", "all_time", "كلي", "دائم", "عام"]):
            time_period = "all_time"
        elif any(w in args_str for w in ["day", "daily", "يوم", "يومي", "اليوم"]):
            time_period = "daily"

        async with ctx.typing():
            async with AsyncSessionLocal() as session:
                service = ActivityService(session)
                embed, file = await service.build_leaderboard(
                    guild=ctx.guild,
                    activity_type=act_type,
                    period=time_period
                )

        view = LeaderboardView(
            guild=ctx.guild,
            current_type=act_type,
            current_period=time_period,
            requester_id=ctx.author.id
        )

        attachments = [file] if file else []
        await ctx.send(embed=embed, files=attachments, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
