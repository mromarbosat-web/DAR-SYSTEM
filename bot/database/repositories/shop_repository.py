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
    # --- 1-24: Anime, Manga, Cyberpunk & Japanese Culture ---
    {"key": "Banner #1", "price": 5000, "emoji": "⚔️", "data": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #2", "price": 5500, "emoji": "🛡️", "data": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #3", "price": 6000, "emoji": "🗡️", "data": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #4", "price": 6500, "emoji": "🪄", "data": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #5", "price": 7000, "emoji": "🔮", "data": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #6", "price": 7500, "emoji": "🌌", "data": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #7", "price": 8000, "emoji": "☄️", "data": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #8", "price": 8500, "emoji": "👾", "data": "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #9", "price": 9000, "emoji": "🤖", "data": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #10", "price": 9500, "emoji": "⛩️", "data": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #11", "price": 10000, "emoji": "🍥", "data": "https://images.unsplash.com/photo-1563089145-599997674d42?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #12", "price": 10500, "emoji": "🌸", "data": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #13", "price": 11000, "emoji": "🏮", "data": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #14", "price": 11500, "emoji": "🍵", "data": "https://images.unsplash.com/photo-1578328819058-b69f3a3b0f6b?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #15", "price": 12000, "emoji": "🐱", "data": "https://images.unsplash.com/photo-1511447333015-45b65e60f6d5?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #16", "price": 12500, "emoji": "⚡", "data": "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #17", "price": 13000, "emoji": "🕹️", "data": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #18", "price": 13500, "emoji": "🐉", "data": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #19", "price": 14000, "emoji": "🎌", "data": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #20", "price": 14500, "emoji": "🗾", "data": "https://images.unsplash.com/photo-1536098561742-ca998e48cbcc?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #21", "price": 15000, "emoji": "🏯", "data": "https://images.unsplash.com/photo-1492571350019-22de08371fd3?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #22", "price": 15500, "emoji": "🌃", "data": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #23", "price": 16000, "emoji": "👘", "data": "https://images.unsplash.com/photo-1524413840807-0c3cb6fa808d?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #24", "price": 16500, "emoji": "🦊", "data": "https://images.unsplash.com/photo-1474511320723-9a56873867b5?w=1200&h=600&fit=crop&q=80"},

    # --- 25-33: Sports & Gaming ---
    {"key": "Banner #25", "price": 6000, "emoji": "🎮", "data": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #26", "price": 6500, "emoji": "🏀", "data": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #27", "price": 7000, "emoji": "🏈", "data": "https://images.unsplash.com/photo-1566577739112-5180d4bf9390?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #28", "price": 8000, "emoji": "🥊", "data": "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #29", "price": 8500, "emoji": "🏎️", "data": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #30", "price": 9000, "emoji": "🛹", "data": "https://images.unsplash.com/photo-1520045892732-304bc3ac5d8e?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #31", "price": 9500, "emoji": "🏄", "data": "https://images.unsplash.com/photo-1502680390469-be75c86b636f?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #32", "price": 10000, "emoji": "⛷️", "data": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #33", "price": 11000, "emoji": "🏆", "data": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=1200&h=600&fit=crop&q=80"},

    # --- 34-42: Islamic Architecture & Culture ---
    {"key": "Banner #34", "price": 8000, "emoji": "🕌", "data": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #35", "price": 8500, "emoji": "🕋", "data": "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #36", "price": 9000, "emoji": "📿", "data": "https://images.unsplash.com/photo-1564769625905-50e93615e769?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #37", "price": 9500, "emoji": "📖", "data": "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #38", "price": 10000, "emoji": "🌙", "data": "https://images.unsplash.com/photo-1532693322450-2cb5c511067d?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #39", "price": 10500, "emoji": "✨", "data": "https://images.unsplash.com/photo-1519710164239-da123dc03ef4?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #40", "price": 11000, "emoji": "🏛️", "data": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #41", "price": 11500, "emoji": "🏮", "data": "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #42", "price": 12000, "emoji": "🕯️", "data": "https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?w=1200&h=600&fit=crop&q=80"},

    # --- 43-51: Nature & Landscapes ---
    {"key": "Banner #43", "price": 7000, "emoji": "🌲", "data": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #44", "price": 7500, "emoji": "⛰️", "data": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #45", "price": 8000, "emoji": "🌊", "data": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #46", "price": 8500, "emoji": "🌸", "data": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #47", "price": 9000, "emoji": "🌅", "data": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #48", "price": 9500, "emoji": "🌴", "data": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #49", "price": 10000, "emoji": "🌻", "data": "https://images.unsplash.com/photo-1597848212624-a19eb35e2651?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #50", "price": 10500, "emoji": "🏞️", "data": "https://images.unsplash.com/photo-1542224566-6e85f2e6772f?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #51", "price": 11000, "emoji": "🍁", "data": "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=1200&h=600&fit=crop&q=80"},

    # --- 52-60: Universe & Space & Natural Wonders ---
    {"key": "Banner #52", "price": 11500, "emoji": "🌿", "data": "https://images.unsplash.com/photo-1518495973542-4542c06a5843?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #53", "price": 12000, "emoji": "🌌", "data": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #54", "price": 12500, "emoji": "🌲", "data": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #55", "price": 13000, "emoji": "🏞️", "data": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #56", "price": 13500, "emoji": "🌋", "data": "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #57", "price": 14000, "emoji": "☄️", "data": "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #58", "price": 15000, "emoji": "🪐", "data": "https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #59", "price": 16000, "emoji": "☀️", "data": "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?w=1200&h=600&fit=crop&q=80"},
    {"key": "Banner #60", "price": 18000, "emoji": "⭐", "data": "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=1200&h=600&fit=crop&q=80"}
]

class ShopRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def seed_default_banner_products(self):
        """Seeds all default banners into the database shop products"""
        try:
            stmt = delete(ShopProduct).where(ShopProduct.type == "BANNER")
            await self.session.execute(stmt)

            for banner in DEFAULT_BANNERS:
                p = ShopProduct(
                    name=banner["key"],
                    price=banner["price"],
                    description="",
                    emoji=banner["emoji"],
                    type="BANNER",
                    data=banner["data"],
                    stock=-1,
                    max_per_user=1,
                    enabled=True,
                    created_at=utc_now(),
                    updated_at=utc_now()
                )
                self.session.add(p)
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
