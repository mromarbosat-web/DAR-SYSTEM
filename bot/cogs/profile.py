import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import Optional, List
from bot.config.settings import settings
from bot.database.connection import AsyncSessionLocal
from bot.services.profile_service import ProfileService
from bot.services.shop_service import ShopService
from bot.database.models.economy import ShopProduct, UserInventory
from bot.utils.embeds import EmbedBuilder
from bot.database.repositories.profile_repository import calculate_level_info, generate_xp_bar

class ChangeBioModal(ui.Modal, title="✏️ Set Status (English Only) [2,000 Aura]"):
    new_bio = ui.TextInput(
        label="Enter your status in English (Required)",
        style=discord.TextStyle.paragraph,
        placeholder="e.g. I am just human",
        required=True,
        max_length=200,
        min_length=2
    )

    def __init__(self, target_member: discord.Member):
        super().__init__()
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            service = ProfileService(session)
            success, msg = await service.set_bio(interaction.user.id, self.new_bio.value)
            if success:
                new_embed = await service.build_profile_embed(self.target_member)
                await interaction.followup.send(embed=EmbedBuilder.success("تم التحديث", msg), ephemeral=True)
            else:
                await interaction.followup.send(embed=EmbedBuilder.error("فشل التحديث", msg), ephemeral=True)

class BannerCarouselView(ui.View):
    """Interactive carousel view for viewing and buying profile banners."""
    def __init__(self, banners: List[ShopProduct], user_id: int, initial_index: int = 0):
        super().__init__(timeout=180)
        self.banners = banners
        self.user_id = user_id
        self.current_index = initial_index
        self.update_buttons()

    def update_buttons(self):
        self.prev_btn.disabled = self.current_index <= 0
        self.next_btn.disabled = self.current_index >= len(self.banners) - 1

    async def get_current_embed(self, user_id: int) -> discord.Embed:
        if not self.banners:
            return EmbedBuilder.info("متجر البانرات", "لا توجد بانرات متاحة حاليًا.")

        banner = self.banners[self.current_index]

        # Check user ownership
        async with AsyncSessionLocal() as session:
            service = ProfileService(session)
            user_banners = await service.get_user_banners(user_id)
            profile = await service.get_profile(user_id)
            owned_ids = [b.product_id for b in user_banners]
            is_owned = banner.product_id in owned_ids
            is_equipped = profile.equipped_banner_id == banner.product_id

        status_text = "⭐ **مجهز حالياً لبروفايلك**" if is_equipped else ("✅ **مملوك في حقيبتك**" if is_owned else "🛒 **غير مملوك**")

        embed = discord.Embed(
            title=f"🖼️ متجر البانرات | {banner.emoji} {banner.name}",
            description=f"**الوصف:** {banner.description}",
            color=discord.Color.from_rgb(138, 43, 226)
        )
        embed.add_field(name="🆔 معرف البانر (ID)", value=f"`#{banner.product_id}`", inline=True)
        embed.add_field(name="💰 السعر", value=f"`{banner.price:,}` {settings.CURRENCY_NAME} {settings.CURRENCY_EMOJI}", inline=True)
        embed.add_field(name="📦 حالة الامتلاك", value=status_text, inline=True)

        if banner.data:
            embed.set_image(url=banner.data)

        embed.set_footer(
            text=f"بانر {self.current_index + 1} من {len(self.banners)} • استخدم الأسهم للتنقل والشراء المباشر"
        )
        return embed

    @ui.button(label="السابق", style=discord.ButtonStyle.secondary, emoji="⬅️", row=0)
    async def prev_btn(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ يمكنك استخدام أزرار المتجر الخاصة بك فقط!", ephemeral=True)
            return
        if self.current_index > 0:
            self.current_index -= 1
            self.update_buttons()
            embed = await self.get_current_embed(interaction.user.id)
            await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="شراء هذا البانر", style=discord.ButtonStyle.success, emoji="🛒", row=0)
    async def buy_btn(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ يمكنك استخدام أزرار المتجر الخاصة بك فقط!", ephemeral=True)
            return

        banner = self.banners[self.current_index]
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            shop_service = ShopService(session)
            member = interaction.guild.get_member(interaction.user.id) or interaction.user
            success, msg, prod = await shop_service.buy_product(interaction.guild, member, banner.product_id)
            if success:
                embed = EmbedBuilder.success("تم الشراء بنجاح", msg)
            else:
                embed = EmbedBuilder.error("فشل الشراء", msg)
            await interaction.followup.send(embed=embed, ephemeral=True)

        # Refresh embed status
        new_embed = await self.get_current_embed(interaction.user.id)
        try:
            await interaction.message.edit(embed=new_embed, view=self)
        except Exception:
            pass

    @ui.button(label="تجهيز للبروفايل", style=discord.ButtonStyle.primary, emoji="✨", row=0)
    async def equip_btn(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ يمكنك استخدام أزرار المتجر الخاصة بك فقط!", ephemeral=True)
            return

        banner = self.banners[self.current_index]
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            service = ProfileService(session)
            success, msg = await service.equip_banner(interaction.user.id, banner.product_id)
            if success:
                embed = EmbedBuilder.success("تم التجهيز", msg)
            else:
                embed = EmbedBuilder.error("فشل التجهيز", msg)
            await interaction.followup.send(embed=embed, ephemeral=True)

        new_embed = await self.get_current_embed(interaction.user.id)
        try:
            await interaction.message.edit(embed=new_embed, view=self)
        except Exception:
            pass

    @ui.button(label="التالي", style=discord.ButtonStyle.secondary, emoji="➡️", row=0)
    async def next_btn(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ يمكنك استخدام أزرار المتجر الخاصة بك فقط!", ephemeral=True)
            return
        if self.current_index < len(self.banners) - 1:
            self.current_index += 1
            self.update_buttons()
            embed = await self.get_current_embed(interaction.user.id)
            await interaction.response.edit_message(embed=embed, view=self)

class ProfileView(ui.View):
    def __init__(self, target_member: discord.Member):
        super().__init__(timeout=180)
        self.target_member = target_member

    @ui.button(label="تعديل الحالة (2,000 أورا)", style=discord.ButtonStyle.primary, emoji="✏️")
    async def edit_bio_btn(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.target_member.id:
            await interaction.response.send_message("❌ يمكنك تعديل حالتك الشخصية فقط في ملفك!", ephemeral=True)
            return
        await interaction.response.send_modal(ChangeBioModal(self.target_member))

    @ui.button(label="متجر وتخصيص البانرات", style=discord.ButtonStyle.success, emoji="🖼️")
    async def banner_shop_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            shop_service = ShopService(session)
            products = await shop_service.list_products(enabled_only=True)
            banners = [p for p in products if p.type in ["BANNER", "COSMETIC"]]

            if not banners:
                await interaction.followup.send("❌ لا توجد بانرات مسجلة في المتجر حالياً.", ephemeral=True)
                return

            carousel = BannerCarouselView(banners, interaction.user.id, 0)
            embed = await carousel.get_current_embed(interaction.user.id)
            await interaction.followup.send(embed=embed, view=carousel, ephemeral=True)

class ProfileCog(commands.Cog):
    """Cog for Member Profile, Leveling, XP, and Customization"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="profile", description="عرض الملف الشخصي الأنيق مع الرصيد والليفل والبانر والحالة")
    @app_commands.describe(user="العضو المراد استعراض ملفه الشخصي (افتراضياً أنت)")
    async def profile_command(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        await interaction.response.defer()
        target = user or interaction.guild.get_member(interaction.user.id) or interaction.user

        if not isinstance(target, discord.Member):
            target = interaction.guild.get_member(target.id) or target

        async with AsyncSessionLocal() as session:
            service = ProfileService(session)
            embed, card_file = await service.build_profile_card_file(target)
            view = ProfileView(target)
            if card_file:
                await interaction.followup.send(file=card_file, view=view)
            else:
                await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="بروفايل", description="عرض الملف الشخصي المتكامل مع الرصيد والليفل والبانر")
    @app_commands.describe(user="العضو المراد استعراض ملفه الشخصي (اختياري)")
    async def arabic_profile_command(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        await self.profile_command.callback(self, interaction, user)

    @app_commands.command(name="banners", description="فتح متجر تصفح وشراء البانرات التفاعلي بالصور والأسهم")
    async def banners_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            shop_service = ShopService(session)
            products = await shop_service.list_products(enabled_only=True)
            banners = [p for p in products if p.type in ["BANNER", "COSMETIC"]]

            if not banners:
                await interaction.followup.send("❌ لا توجد بانرات مسجلة في المتجر حالياً.", ephemeral=True)
                return

            carousel = BannerCarouselView(banners, interaction.user.id, 0)
            embed = await carousel.get_current_embed(interaction.user.id)
            await interaction.followup.send(embed=embed, view=carousel, ephemeral=True)

    @app_commands.command(name="setbio", description="تغيير وتخصيص حالتك في الملف الشخصي مقابل 2,000 أورا")
    @app_commands.describe(bio="الحالة الجديدة المراد وضعها (الحد الأقصى 200 حرف)")
    async def set_bio_command(self, interaction: discord.Interaction, bio: str):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            service = ProfileService(session)
            success, msg = await service.set_bio(interaction.user.id, bio)
            if success:
                embed = EmbedBuilder.success("تم تحديث الحالة", msg)
            else:
                embed = EmbedBuilder.error("فشل التحديث", msg)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="setbanner", description="تجهيز بانر لملفك الشخصي من حقيبتك")
    @app_commands.describe(product_id="معرف البانر (Product ID)")
    async def set_banner_command(self, interaction: discord.Interaction, product_id: int):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            service = ProfileService(session)
            success, msg = await service.equip_banner(interaction.user.id, product_id)
            if success:
                embed = EmbedBuilder.success("تم تجهيز البانر", msg)
            else:
                embed = EmbedBuilder.error("فشل تجهيز البانر", msg)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="rank", description="عرض مستواك وترتيبك في نقاط الخبرة (XP) والتفاعل")
    @app_commands.describe(user="العضو المراد استعلام مستواه (اختياري)")
    async def rank_command(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        await interaction.response.defer()
        target = user or interaction.guild.get_member(interaction.user.id) or interaction.user

        async with AsyncSessionLocal() as session:
            service = ProfileService(session)
            profile = await service.get_profile(target.id)
            rank = await service.profile_repo.get_user_rank(target.id)

            level, cur_xp, needed_xp, progress = calculate_level_info(profile.xp)
            xp_bar = generate_xp_bar(progress, length=10)

            embed = discord.Embed(
                title=f"⭐ بطاقة المستوى والخبرة | {target.name}",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.add_field(name="المستوى (Level)", value=f"**`{level}`**", inline=True)
            embed.add_field(name="الترتيب (Rank)", value=f"**`#{rank}`**", inline=True)
            embed.add_field(name="إجمالي نقاط XP", value=f"**`{profile.xp:,}`** XP", inline=True)
            embed.add_field(name="التقدم للمستوى القادم", value=f"`{cur_xp:,}` / `{needed_xp:,}` XP\n{xp_bar}", inline=False)
            embed.set_footer(text=f"الرسائل المسجلة: {profile.messages_count:,}")

            await interaction.followup.send(embed=embed)

    @app_commands.command(name="levels", description="عرض لائحة متصدري المستويات ونقاط الخبرة (XP Leaderboard)")
    async def levels_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            service = ProfileService(session)
            top_profiles = await service.profile_repo.get_xp_leaderboard(limit=10)

            if not top_profiles:
                embed = EmbedBuilder.info("لائحة المتصدرين", "لا توجد مستويات مسجلة بعد.")
            else:
                lines = []
                for idx, p in enumerate(top_profiles, start=1):
                    medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"`#{idx}`"
                    lvl, _, _, _ = calculate_level_info(p.xp)
                    lines.append(f"{medal} <@{p.user_id}> — **المستوى {lvl}** (`{p.xp:,}` XP)")

                embed = EmbedBuilder.info(
                    title="⭐ لائحة أعلى المستويات والنشاط (Levels Leaderboard)",
                    description="\n".join(lines)
                )

            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))
