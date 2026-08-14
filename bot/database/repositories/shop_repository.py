import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.time import utc_now
from bot.config.settings import settings
from bot.database.models.economy import ShopProduct, UserInventory, Wallet, Transaction

logger = logging.getLogger("discord_bot.shop_repository")

DEFAULT_BANNERS = [
    {
        "name": "🌌 بانر الفضاء الكوني (Cosmic Galaxy)",
        "price": 10000,
        "description": "بانر فلكي نقي من أعماق الفضاء الخارجي لملفك الشخصي.",
        "emoji": "🌌",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "⚡ بانر السايبربانك النيون (Neon Cyberpunk)",
        "price": 12500,
        "description": "بانر مستقبلي بأضواء نيون سايبربانك مشعة.",
        "emoji": "⚡",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🌅 بانر الشفق الذهبي (Golden Twilight)",
        "price": 15000,
        "description": "بانر ساحر لشفق الغروب الذهبي الفاخر.",
        "emoji": "🌅",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🐉 بانر التنين الملكي (Imperial Dragon)",
        "price": 17500,
        "description": "بانر أسطوري بقوة وهيبة التنين الإمبراطوري.",
        "emoji": "🐉",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "👑 بانر الفخامة المظلمة (Dark Luxury Aura)",
        "price": 20000,
        "description": "بانر فخم ونادر مرصع بهالة مظلمة وملكية لا تضاهى.",
        "emoji": "👑",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=1000&auto=format&fit=crop&q=80"
    }
]

class ShopRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def seed_default_banner_products(self):
        """Seeds default customizable profile banners if not present"""
        for banner in DEFAULT_BANNERS:
            stmt = select(ShopProduct).where(ShopProduct.name == banner["name"])
            res = await self.session.execute(stmt)
            if not res.scalar_one_or_none():
                p = ShopProduct(
                    name=banner["name"],
                    price=banner["price"],
                    description=banner["description"],
                    emoji=banner["emoji"],
                    type=banner["type"],
                    data=banner["data"],
                    stock=-1,
                    max_per_user=1,
                    enabled=True,
                    created_at=utc_now(),
                    updated_at=utc_now()
                )
                self.session.add(p)
        try:
            await self.session.commit()
        except Exception as e:
            logger.warning(f"Failed to seed default banners: {e}")
            await self.session.rollback()

    async def get_product(self, product_id: int) -> Optional[ShopProduct]:
        stmt = select(ShopProduct).where(ShopProduct.product_id == product_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_products(self, enabled_only: bool = True) -> List[ShopProduct]:
        stmt = select(ShopProduct)
        if enabled_only:
            stmt = stmt.where(ShopProduct.enabled == True)
        stmt = stmt.order_by(ShopProduct.product_id.asc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def create_product(
        self,
        name: str,
        price: int,
        description: Optional[str] = None,
        emoji: Optional[str] = "📦",
        stock: int = -1,
        max_per_user: int = -1,
        type: str = "ROLE",
        role_id: Optional[int] = None,
        data: Optional[str] = None,
        enabled: bool = True
    ) -> ShopProduct:
        product = ShopProduct(
            name=name,
            price=price,
            description=description,
            emoji=emoji or "📦",
            stock=stock,
            max_per_user=max_per_user,
            type=type.upper().strip(),
            role_id=role_id,
            data=data,
            enabled=enabled,
            created_at=utc_now(),
            updated_at=utc_now()
        )
        self.session.add(product)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def update_product(self, product_id: int, **kwargs) -> Optional[ShopProduct]:
        product = await self.get_product(product_id)
        if not product:
            return None

        for key, val in kwargs.items():
            if hasattr(product, key) and val is not None:
                setattr(product, key, val)
        product.updated_at = utc_now()
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def delete_product(self, product_id: int) -> bool:
        product = await self.get_product(product_id)
        if not product:
            return False
        await self.session.delete(product)
        await self.session.commit()
        return True

    async def get_user_inventory(self, user_id: int) -> List[Tuple[ShopProduct, int]]:
        stmt = select(ShopProduct, UserInventory.quantity).join(
            UserInventory, ShopProduct.product_id == UserInventory.product_id
        ).where(UserInventory.user_id == user_id)
        res = await self.session.execute(stmt)
        return list(res.all())

    async def get_user_item_count(self, user_id: int, product_id: int) -> int:
        stmt = select(UserInventory.quantity).where(
            UserInventory.user_id == user_id,
            UserInventory.product_id == product_id
        )
        res = await self.session.execute(stmt)
        qty = res.scalar_one_or_none()
        return qty or 0

    async def purchase_product_atomic(self, user_id: int, product_id: int) -> Tuple[bool, str, Optional[ShopProduct]]:
        """
        Atomically handles wallet deduction, stock decrement, inventory increment, and transaction recording.
        """
        try:
            # Lock product and wallet
            stmt_p = select(ShopProduct).where(ShopProduct.product_id == product_id).with_for_update()
            res_p = await self.session.execute(stmt_p)
            product = res_p.scalar_one_or_none()

            if not product or not product.enabled:
                await self.session.rollback()
                return False, "هذا المنتج غير متاح في المتجر حاليًا!", None

            if product.stock == 0:
                await self.session.rollback()
                return False, "عذرًا، نفد مخزون هذا المنتج بالكامل!", product

            # Check max per user
            current_qty = await self.get_user_item_count(user_id, product_id)
            if product.max_per_user > 0 and current_qty >= product.max_per_user:
                await self.session.rollback()
                return False, f"لقد وصلت للحد الأقصى المسموح بشرائه لهذا المنتج (`{product.max_per_user}` قطعة)!", product

            # Check wallet
            stmt_w = select(Wallet).where(Wallet.user_id == user_id).with_for_update()
            res_w = await self.session.execute(stmt_w)
            wallet = res_w.scalar_one_or_none()

            if not wallet or wallet.balance < product.price:
                curr_bal = wallet.balance if wallet else 0
                await self.session.rollback()
                return False, f"رصيدك الحالي (`{curr_bal}` {settings.CURRENCY_NAME}) غير كافٍ لشراء هذا المنتج (`{product.price}` {settings.CURRENCY_NAME})!", product

            # Deduct wallet
            b_before = wallet.balance
            wallet.balance -= product.price
            wallet.updated_at = datetime.now(timezone.utc)

            # Decrement stock if not unlimited (-1)
            if product.stock > 0:
                product.stock -= 1

            # Update inventory
            stmt_inv = select(UserInventory).where(
                UserInventory.user_id == user_id,
                UserInventory.product_id == product_id
            ).with_for_update()
            res_inv = await self.session.execute(stmt_inv)
            inv_item = res_inv.scalar_one_or_none()

            if inv_item:
                inv_item.quantity += 1
                inv_item.updated_at = datetime.now(timezone.utc)
            else:
                inv_item = UserInventory(user_id=user_id, product_id=product_id, quantity=1)
                self.session.add(inv_item)

            # Record transaction
            tx = Transaction(
                user_id=user_id,
                guild_id=None,
                type="PURCHASE",
                amount=-product.price,
                balance_before=b_before,
                balance_after=wallet.balance,
                reason=f"Bought item #{product.product_id}: {product.name}"
            )
            self.session.add(tx)
            await self.session.commit()

            return True, f"تم شراء `{product.name}` بنجاح بسعر `{product.price}` {settings.CURRENCY_NAME}!", product
        except Exception as e:
            logger.error(f"Error in purchase: {e}")
            await self.session.rollback()
            return False, "حدث خطأ أثناء إتمام عملية الشراء.", None
