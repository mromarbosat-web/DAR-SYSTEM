import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from bot.config.settings import settings
from bot.database.connection import AsyncSessionLocal
from bot.services.shop_service import ShopService
from bot.utils.embeds import EmbedBuilder

class ShopCog(commands.Cog):
    """Cog for Shop User & Admin Commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    shop_admin_group = app_commands.Group(name="shop_admin", description="إدارة وتعديل معروضات ومنتجات المتجر")

    @app_commands.command(name="shop", description="استعراض قائمة معروضات ومنتجات المتجر للعملة")
    async def shop_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            shop_service = ShopService(session)
            products = await shop_service.list_products(enabled_only=True)

            if not products:
                embed = EmbedBuilder.info(
                    title=f"🛒 متجر السيرفر - {settings.CURRENCY_NAME}",
                    description="لا توجد منتجات معروضة حاليًا في المتجر. ترقبوا الإضافات القادمة!"
                )
            else:
                fields = []
                for p in products:
                    stk_str = "غير محدود" if p.stock < 0 else f"`{p.stock}` قطعة"
                    max_str = f" | الحد: `{p.max_per_user}`/شخص" if p.max_per_user > 0 else ""
                    desc = f"{p.description}\n" if p.description else ""

                    fields.append((
                        f"{p.emoji} {p.name} — #{p.product_id}",
                        f"{desc}💰 **السعر:** `{p.price:,}` {settings.CURRENCY_NAME}\n📦 **المخزون:** {stk_str}{max_str}\n🛒 **للشراء:** `/buy product_id:{p.product_id}`",
                        False
                    ))

                embed = EmbedBuilder.info(
                    title=f"🛒 متجر السيرفر الرئيسي - {settings.CURRENCY_NAME} {settings.CURRENCY_EMOJI}",
                    description=f"استخدم أزرار وأوامر الشراء لاقتناء الرتب والمنتجات باستعمال عملتك **{settings.CURRENCY_NAME}**:",
                    fields=fields
                )

            await interaction.followup.send(embed=embed)

    @app_commands.command(name="buy", description="شراء منتج من المتجر باستخدام الـ ID")
    @app_commands.describe(product_id="رقم معرف المنتج (Product ID)")
    async def buy_command(self, interaction: discord.Interaction, product_id: int):
        await interaction.response.defer()

        async with AsyncSessionLocal() as session:
            shop_service = ShopService(session)
            success, msg = await shop_service.buy_product(interaction.guild, interaction.user, product_id)

            if success:
                embed = EmbedBuilder.success("تمت عملية الشراء", msg)
            else:
                embed = EmbedBuilder.error("فشلت عملية الشراء", msg)

            await interaction.followup.send(embed=embed)

    # --- ADMIN SHOP COMMANDS ---

    @shop_admin_group.command(name="add", description="[إداري] إضافة منتج جديد لمتجر السيرفر")
    @app_commands.describe(
        name="اسم المنتج",
        price="السعر بالعملة",
        description="وصف اختياري للمنتج",
        emoji="الإيموجي المخصص للمنتج",
        stock="المخزون المتاح (-1 لغير محدود)",
        max_per_user="الحد الأقصى للشخص الواحد (-1 لغير محدود)",
        type="نوع المنتج (ROLE / ITEM / COSMETIC)",
        role="الرتبة المراد تسليمها تلقائيًا (إذا كان نوع المنتج ROLE)"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="Role (تسليم رتبة ديسكورد تلقائيًا)", value="ROLE"),
        app_commands.Choice(name="Item (غرض افتراضي في الحقيبة)", value="ITEM"),
        app_commands.Choice(name="Cosmetic (مظهر كوزمتك)", value="COSMETIC"),
    ])
    async def shop_add(
        self,
        interaction: discord.Interaction,
        name: str,
        price: int,
        description: Optional[str] = None,
        emoji: Optional[str] = "📦",
        stock: int = -1,
        max_per_user: int = -1,
        type: app_commands.Choice[str] = None,
        role: Optional[discord.Role] = None
    ):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            shop_service = ShopService(session)
            product_type = type.value if type else "ROLE"

            success, msg, _ = await shop_service.add_product(
                admin_member=interaction.user,
                name=name,
                price=price,
                description=description,
                emoji=emoji,
                stock=stock,
                max_per_user=max_per_user,
                product_type=product_type,
                role=role
            )

            if success:
                embed = EmbedBuilder.success("تمت الإضافة", msg)
            else:
                embed = EmbedBuilder.error("فشلت الإضافة", msg)

            await interaction.followup.send(embed=embed, ephemeral=True)

    @shop_admin_group.command(name="edit", description="[إداري] تعديل بيانات منتج موجود في المتجر")
    @app_commands.describe(
        product_id="معرف المنتج المراد تعديله",
        name="الاسم الجديد",
        price="السعر الجديد",
        description="الوصف الجديد",
        emoji="الإيموجي الجديد",
        stock="المخزون الجديد",
        enabled="تفعيل أو تعطيل ظهور المنتج بالمتجر"
    )
    async def shop_edit(
        self,
        interaction: discord.Interaction,
        product_id: int,
        name: Optional[str] = None,
        price: Optional[int] = None,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        stock: Optional[int] = None,
        enabled: Optional[bool] = None
    ):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            shop_service = ShopService(session)
            kwargs = {}
            if name: kwargs["name"] = name
            if price is not None: kwargs["price"] = price
            if description: kwargs["description"] = description
            if emoji: kwargs["emoji"] = emoji
            if stock is not None: kwargs["stock"] = stock
            if enabled is not None: kwargs["enabled"] = enabled

            success, msg, _ = await shop_service.edit_product(interaction.user, product_id, **kwargs)

            if success:
                embed = EmbedBuilder.success("تم التعديل", msg)
            else:
                embed = EmbedBuilder.error("فشل التعديل", msg)

            await interaction.followup.send(embed=embed, ephemeral=True)

    @shop_admin_group.command(name="remove", description="[إداري] حذف منتج نهائيًا من المتجر")
    @app_commands.describe(product_id="معرف المنتج المراد حسفه")
    async def shop_remove(self, interaction: discord.Interaction, product_id: int):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            shop_service = ShopService(session)
            success, msg = await shop_service.remove_product(interaction.user, product_id)

            if success:
                embed = EmbedBuilder.success("تم الحذف", msg)
            else:
                embed = EmbedBuilder.error("فشل الحذف", msg)

            await interaction.followup.send(embed=embed, ephemeral=True)

    @shop_admin_group.command(name="list", description="[إداري] عرض كافة المنتجات المتاحة والغير متاحة بالمتجر")
    async def shop_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            shop_service = ShopService(session)
            products = await shop_service.list_products(enabled_only=False)

            if not products:
                embed = EmbedBuilder.info("قائمة المتجر الكاملة", "لا توجد أي منتجات مضافة في النظام.")
            else:
                fields = []
                for p in products:
                    status = "مفعل ✅" if p.enabled else "معطل ❌"
                    fields.append((
                        f"{p.emoji} {p.name} (#{p.product_id})",
                        f"السعر: `{p.price}` | المخزون: `{p.stock}` | الحالة: {status} | النوع: `{p.type}`",
                        False
                    ))

                embed = EmbedBuilder.info(
                    title="📋 قائمة كافة معروضات المتجر للإدارة",
                    description="تشمل المعروضات المفعلة والمخفية:",
                    fields=fields
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))
