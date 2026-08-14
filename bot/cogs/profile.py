import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
from bot.config.settings import settings
from bot.database.connection import AsyncSessionLocal
from bot.services.profile_service import ProfileService
from bot.services.shop_service import ShopService
from bot.utils.embeds import EmbedBuilder
from bot.database.repositories.profile_repository import calculate_level_info, generate_xp_bar

class ChangeBioModal(discord.ui.Modal, title="✏️ تعديل الحالة الشخصية (2,000 أورا)"):
    new_bio = discord.ui.TextInput(
        label="اكتب حالتك الجديدة (Custom Status)",
        style=discord.TextStyle.paragraph,
        placeholder="أدخل حالتك أو حكمتك المميزة هنا...",
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

class BannerSelect(discord.ui.Select):
    def __init__(self, banners: list, target_member: discord.Member):
        options = []
        for b in banners[:25]:
            options.append(
                discord.SelectOption(
                    label=b.name[:100],
                    value=str(b.product_id),
                    description=f"بانر رقم #{b.product_id}",
                    emoji="🖼️"
                )
            )
        super().__init__(
            placeholder="اختر البانر الذي ترغب بتجهيزه لملفك الشخصي...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.target_member = target_member

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.target_member.id:
            await interaction.response.send_message("❌ هذا الخيار مخصص لصاحب الملف الشخصي فقط!", ephemeral=True)
            return

        product_id = int(self.values[0])
        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            service = ProfileService(session)
            success, msg = await service.equip_banner(interaction.user.id, product_id)
            if success:
                new_embed = await service.build_profile_embed(self.target_member)
                await interaction.followup.send(embed=EmbedBuilder.success("تم التجهيز", msg), ephemeral=True)
            else:
                await interaction.followup.send(embed=EmbedBuilder.error("خطأ", msg), ephemeral=True)

class SelectBannerView(discord.ui.View):
    def __init__(self, banners: list, target_member: discord.Member):
        super().__init__(timeout=120)
        self.add_item(BannerSelect(banners, target_member))

class ProfileView(discord.ui.View):
    def __init__(self, target_member: discord.Member):
        super().__init__(timeout=180)
        self.target_member = target_member

    @discord.ui.button(label="تعديل الحالة (2,000 أورا)", style=discord.ButtonStyle.primary, emoji="✏️")
    async def edit_bio_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_member.id:
            await interaction.response.send_message("❌ يمكنك تعديل حالتك الشخصية فقط في ملفك!", ephemeral=True)
            return
        await interaction.response.send_modal(ChangeBioModal(self.target_member))

    @discord.ui.button(label="تبديل البانر", style=discord.ButtonStyle.secondary, emoji="🖼️")
    async def change_banner_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_member.id:
            await interaction.response.send_message("❌ هذا الزر مخصص لصاحب الملف فقط!", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            service = ProfileService(session)
            banners = await service.get_user_banners(interaction.user.id)
            if not banners:
                await interaction.response.send_message(
                    "❌ أنت لا تملك أي بانرات في حقيبتك حاليًا!\n🛒 يمكنك شراء بانرات مميزة من المتجر بأسعار تبدأ من 10,000 أورا عبر زر 'متجر البانرات'.",
                    ephemeral=True
                )
                return

            view = SelectBannerView(banners, self.target_member)
            await interaction.response.send_message("🖼️ اختر البانر المراد عرضه في بروفايلك:", view=view, ephemeral=True)

    @discord.ui.button(label="متجر البانرات", style=discord.ButtonStyle.success, emoji="🛒")
    async def banner_shop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with AsyncSessionLocal() as session:
            shop_service = ShopService(session)
            products = await shop_service.list_products(enabled_only=True)
            banner_prods = [p for p in products if p.type in ["BANNER", "COSMETIC"]]

            embed = discord.Embed(
                title=f"🛒 متجر بانرات البروفايل - {settings.CURRENCY_NAME} {settings.CURRENCY_EMOJI}",
                description="بانرات فخمة ومميزة لتزيين ملفك الشخصي. أسعار البانرات تتراوح بين 10,000 إلى 20,000 أورا:",
                color=discord.Color.purple()
            )

            for b in banner_prods:
                embed.add_field(
                    name=f"{b.emoji} {b.name} (معرف: `#{b.product_id}`)",
                    value=f"• **السعر:** `{b.price:,}` {settings.CURRENCY_NAME}\n• **الوصف:** {b.description}\n• **للشراء:** `/buy product_id:{b.product_id}`",
                    inline=False
                )

            embed.set_footer(text="بعد الشراء، يمكنك تجهيز البانر مباشرة عبر زر 'تبديل البانر' أو أمر /setbanner")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class ProfileCog(commands.Cog):
    """Cog for Member Profile, Leveling, XP, and Customization"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="profile", description="عرض الملف الشخصي المتكامل مع الرصيد والليفل والبانر والحالة")
    @app_commands.describe(user="العضو المراد استعراض ملفه الشخصي (افتراضياً أنت)")
    async def profile_command(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        await interaction.response.defer()
        target = user or interaction.guild.get_member(interaction.user.id) or interaction.user

        if not isinstance(target, discord.Member):
            target = interaction.guild.get_member(target.id) or target

        async with AsyncSessionLocal() as session:
            service = ProfileService(session)
            embed = await service.build_profile_embed(target)
            view = ProfileView(target)
            await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="بروفايل", description="عرض الملف الشخصي المتكامل مع الرصيد والليفل والبانر")
    @app_commands.describe(user="العضو المراد استعراض ملفه الشخصي (اختياري)")
    async def arabic_profile_command(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        await self.profile_command.callback(self, interaction, user)

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
            xp_bar = generate_xp_bar(progress, length=12)

            embed = discord.Embed(
                title=f"⭐ بطاقة المستوى والخبرة | {target.display_name}",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.add_field(name="المستوى (Level)", value=f"**`{level}`**", True)
            embed.add_field(name="الترتيب (Rank)", value=f"**`#{rank}`**", True)
            embed.add_field(name="إجمالي نقاط XP", value=f"**`{profile.xp:,}`** XP", True)
            embed.add_field(name="التقدم للمستوى القادم", value=f"`{cur_xp:,}` / `{needed_xp:,}` XP\n{xp_bar}", False)
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
