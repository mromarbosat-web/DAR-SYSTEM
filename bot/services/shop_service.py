import logging
from typing import List, Tuple, Optional
import discord
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config.settings import settings
from bot.database.repositories.shop_repository import ShopRepository
from bot.services.permission_service import PermissionService
from bot.services.log_service import LogService
from bot.database.models.economy import ShopProduct
from bot.utils.embeds import EmbedBuilder

logger = logging.getLogger("discord_bot.shop_service")

class ShopService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.shop_repo = ShopRepository(session)
        self.perm_service = PermissionService(session)
        self.log_service = LogService(session)

    async def list_products(self, enabled_only: bool = True) -> List[ShopProduct]:
        # Ensure default banners are seeded
        await self.shop_repo.seed_default_banner_products()
        return await self.shop_repo.list_products(enabled_only=enabled_only)

    async def add_product(
        self,
        admin_member: discord.Member,
        name: str,
        price: int,
        description: Optional[str] = None,
        emoji: Optional[str] = "📦",
        stock: int = -1,
        max_per_user: int = -1,
        product_type: str = "ROLE",
        role: Optional[discord.Role] = None,
        data: Optional[str] = None
    ) -> Tuple[bool, str, Optional[ShopProduct]]:
        if not await self.perm_service.has_manager_permission(admin_member, "SHOP_MANAGER"):
            return False, "ليس لديك صلاحية إدارة المتجر (`SHOP_MANAGER`)!", None

        if price <= 0:
            return False, "سعر المنتج يجب أن يكون أكبر من 0!", None

        role_id = role.id if role else None

        product = await self.shop_repo.create_product(
            name=name,
            price=price,
            description=description,
            emoji=emoji,
            stock=stock,
            max_per_user=max_per_user,
            type=product_type,
            role_id=role_id,
            data=data
        )

        log_embed = EmbedBuilder.success(
            title="إضافة منتج جديد للمتجر (Shop Product Added)",
            description=f"قام الإداري {admin_member.mention} بفيادة وإضافة منتج جديد للمتجر.",
            fields=[
                ("معرف المنتج", f"`#{product.product_id}`", True),
                ("الاسم", f"{product.emoji} {product.name}", True),
                ("السعر", f"`{product.price}` {settings.CURRENCY_NAME}", True),
                ("النوع", f"`{product.type}`", True)
            ]
        )
        await self.log_service.log_event(admin_member.guild, "economy", log_embed)
        return True, f"تمت إضافة المنتج `{product.name}` (ID: `#{product.product_id}`) للمتجر بنجاح!", product

    async def edit_product(
        self,
        admin_member: discord.Member,
        product_id: int,
        **kwargs
    ) -> Tuple[bool, str, Optional[ShopProduct]]:
        if not await self.perm_service.has_manager_permission(admin_member, "SHOP_MANAGER"):
            return False, "ليس لديك صلاحية إدارة المتجر (`SHOP_MANAGER`)!", None

        product = await self.shop_repo.update_product(product_id, **kwargs)
        if not product:
            return False, f"لم يتم العثور على منتج يحمل الـ ID `#{product_id}`!", None

        log_embed = EmbedBuilder.info(
            title="تحديث منتج في المتجر (Product Updated)",
            description=f"قام الإداري {admin_member.mention} بتحديث بيانات المنتج `#{product_id}`.",
            fields=[
                ("المنتج", f"{product.emoji} {product.name}", True),
                ("السعر الحالي", f"`{product.price}` {settings.CURRENCY_NAME}", True)
            ]
        )
        await self.log_service.log_event(admin_member.guild, "economy", log_embed)
        return True, f"تم تحديث بيانات المنتج `{product.name}` بنجاح!", product

    async def remove_product(
        self,
        admin_member: discord.Member,
        product_id: int
    ) -> Tuple[bool, str]:
        if not await self.perm_service.has_manager_permission(admin_member, "SHOP_MANAGER"):
            return False, "ليس لديك صلاحية إدارة المتجر (`SHOP_MANAGER`)!"

        product = await self.shop_repo.get_product(product_id)
        if not product:
            return False, f"لم يتم العثور على منتج بالمعرف `#{product_id}`!"

        deleted = await self.shop_repo.delete_product(product_id)
        if deleted:
            log_embed = EmbedBuilder.error(
                title="حذف منتج من المتجر (Product Removed)",
                description=f"قام الإداري {admin_member.mention} بحذف المنتج `#{product_id}` ({product.name})."
            )
            await self.log_service.log_event(admin_member.guild, "economy", log_embed)
            return True, f"تم حذف المنتج `{product.name}` من المتجر بنجاح."

        return False, "فشلت عملية حذف المنتج."

    async def buy_product(
        self,
        guild: discord.Guild,
        member: discord.Member,
        product_id: int
    ) -> Tuple[bool, str]:
        success, msg, product = await self.shop_repo.purchase_product_atomic(member.id, product_id)
        if not success or not product:
            return False, msg

        extra_msg = ""
        # If product type is ROLE, try granting role automatically on Discord
        if product.type == "ROLE" and product.role_id:
            role = guild.get_role(product.role_id)
            if role:
                try:
                    await member.add_roles(role, reason=f"Purchased from shop (#{product.product_id})")
                    extra_msg = f"\n✅ وتم منحك رتبة {role.mention} تلقائيًا في السيرفر!"
                except discord.Forbidden:
                    extra_msg = f"\n⚠️ تم الشراء ولكن تعذر إعطاؤك رتبة {role.name} تلقائيًا بسبب نقص صلاحيات البوت. يرجى التواصل مع الإدارة."
                except Exception as e:
                    logger.error(f"Failed auto assigning purchased role: {e}")
                    extra_msg = f"\n⚠️ تم الشراء ولكن حدث خطأ أثناء تسليم الرتبة."

        # If product type is BANNER, automatically notify about equip
        if product.type == "BANNER":
            extra_msg = f"\n🖼️ يمكنك تجهيز هذا البانر لملفك الشخصي عبر أمر `/setbanner` أو زر تبديل البانر في `/profile`!"

        # Log purchase
        log_embed = EmbedBuilder.info(
            title="عملية شراء من المتجر (Shop Purchase)",
            description=f"شراء العضو {member.mention} لمُنتج من المتجر.",
            fields=[
                ("العضو الشاري", f"{member} (`{member.id}`)", True),
                ("المنتج", f"{product.emoji} {product.name} (`#{product.product_id}`)", True),
                ("المبلغ المدفوع", f"`{product.price}` {settings.CURRENCY_NAME}", True)
            ]
        )
        await self.log_service.log_event(guild, "economy", log_embed)

        return True, f"{msg}{extra_msg}"

    async def get_user_inventory(self, user_id: int) -> List[Tuple[ShopProduct, int]]:
        return await self.shop_repo.get_user_inventory(user_id)
