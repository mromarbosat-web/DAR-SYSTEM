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
    # --- 1. LIGHT & NATURE BANNERS (15 Banners) ---
    {"name": "ندى الصباح", "price": 8000, "description": "", "emoji": "🌿", "type": "BANNER", "data": "https://images.unsplash.com/photo-1511497584788-876761142197?w=1200&h=600&fit=crop&q=80"},
    {"name": "أفق واسع", "price": 8500, "description": "", "emoji": "🌅", "type": "BANNER", "data": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&h=600&fit=crop&q=80"},
    {"name": "نهر هادئ", "price": 9000, "description": "", "emoji": "🏞️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1542224566-6e85f2e6772f?w=1200&h=600&fit=crop&q=80"},
    {"name": "سهوب خضراء", "price": 7500, "description": "", "emoji": "🌾", "type": "BANNER", "data": "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=1200&h=600&fit=crop&q=80"},
    {"name": "زهور برية", "price": 7000, "description": "", "emoji": "🌸", "type": "BANNER", "data": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=1200&h=600&fit=crop&q=80"},
    {"name": "جبال الألب", "price": 9500, "description": "", "emoji": "🏔️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=1200&h=600&fit=crop&q=80"},
    {"name": "سد مائي", "price": 9000, "description": "", "emoji": "🌊", "type": "BANNER", "data": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&h=600&fit=crop&q=80"},
    {"name": "شاطئ عاجي", "price": 10000, "description": "", "emoji": "🏝️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&h=600&fit=crop&q=80"},
    {"name": "سماء ناعمة", "price": 7500, "description": "", "emoji": "⛅", "type": "BANNER", "data": "https://images.unsplash.com/photo-1513002749550-c59d786b8e6c?w=1200&h=600&fit=crop&q=80"},
    {"name": "نخيل باسقة", "price": 8000, "description": "", "emoji": "🌴", "type": "BANNER", "data": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1200&h=600&fit=crop&q=80"},
    {"name": "غروب ساحر", "price": 8500, "description": "", "emoji": "🌇", "type": "BANNER", "data": "https://images.unsplash.com/photo-1495616811223-4d98c6e9c869?w=1200&h=600&fit=crop&q=80"},
    {"name": "أوراق متساقطة", "price": 7500, "description": "", "emoji": "🍂", "type": "BANNER", "data": "https://images.unsplash.com/photo-1507371341992-2b5e87a2d23a?w=1200&h=600&fit=crop&q=80"},
    {"name": "أضواء المدينة", "price": 9000, "description": "", "emoji": "🏙️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=1200&h=600&fit=crop&q=80"},
    {"name": "طبيعة عذراء", "price": 8500, "description": "", "emoji": "🌿", "type": "BANNER", "data": "https://images.unsplash.com/photo-1426604966848-d7adacbd02bff?w=1200&h=600&fit=crop&q=80"},
    {"name": "غيوم متراكمة", "price": 8000, "description": "", "emoji": "☁️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=1200&h=600&fit=crop&q=80"},

    # --- 2. DARK & MYSTERIOUS BANNERS (15 Banners) ---
    {"name": "مجرة درب", "price": 11000, "description": "", "emoji": "🌌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&h=600&fit=crop&q=80"},
    {"name": "نيون أزرق", "price": 12000, "description": "", "emoji": "⚡", "type": "BANNER", "data": "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=1200&h=600&fit=crop&q=80"},
    {"name": "قمر مظلم", "price": 13000, "description": "", "emoji": "🌑", "type": "BANNER", "data": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1200&h=600&fit=crop&q=80"},
    {"name": "كهف عميق", "price": 10500, "description": "", "emoji": "🦇", "type": "BANNER", "data": "https://images.unsplash.com/photo-1519751138087-5bf79df62d5b?w=1200&h=600&fit=crop&q=80"},
    {"name": "سديم فضائي", "price": 12500, "description": "", "emoji": "✨", "type": "BANNER", "data": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&h=600&fit=crop&q=80"},
    {"name": "ليل صامت", "price": 11000, "description": "", "emoji": "🌙", "type": "BANNER", "data": "https://images.unsplash.com/photo-1532693322450-2cb5c511067d?w=1200&h=600&fit=crop&q=80"},
    {"name": "ظل غامض", "price": 11500, "description": "", "emoji": "👤", "type": "BANNER", "data": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=1200&h=600&fit=crop&q=80"},
    {"name": "أشجار داكنة", "price": 10000, "description": "", "emoji": "🌲", "type": "BANNER", "data": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200&h=600&fit=crop&q=80"},
    {"name": "ثقب دودي", "price": 15000, "description": "", "emoji": "🕳️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1502134249126-9f3755a50d78?w=1200&h=600&fit=crop&q=80"},
    {"name": "أطياف الليل", "price": 12000, "description": "", "emoji": "👻", "type": "BANNER", "data": "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=1200&h=600&fit=crop&q=80"},
    {"name": "عالم سحري", "price": 13500, "description": "", "emoji": "🔮", "type": "BANNER", "data": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=1200&h=600&fit=crop&q=80"},
    {"name": "أزقة ليلية", "price": 11000, "description": "", "emoji": "🌃", "type": "BANNER", "data": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1200&h=600&fit=crop&q=80"},
    {"name": "شهب ساطعة", "price": 14000, "description": "", "emoji": "☄️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1200&h=600&fit=crop&q=80"},
    {"name": "محيط مظلم", "price": 11500, "description": "", "emoji": "🌊", "type": "BANNER", "data": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1200&h=600&fit=crop&q=80"},
    {"name": "طاقة خفية", "price": 14500, "description": "", "emoji": "🖤", "type": "BANNER", "data": "https://images.unsplash.com/photo-1515260268569-9271009adfdb?w=1200&h=600&fit=crop&q=80"},

    # --- 3. ISLAMIC BANNERS (Mosques & Prayer Rugs - 15 Banners) ---
    {"name": "سجاد تركي", "price": 9000, "description": "", "emoji": "🕌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=1200&h=600&fit=crop&q=80"},
    {"name": "جامع كبير", "price": 10000, "description": "", "emoji": "🕌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=1200&h=600&fit=crop&q=80"},
    {"name": "مصباح تراثي", "price": 8500, "description": "", "emoji": "✨", "type": "BANNER", "data": "https://images.unsplash.com/photo-1519710164239-da123dc03ef4?w=1200&h=600&fit=crop&q=80"},
    {"name": "قبة عثمانية", "price": 11000, "description": "", "emoji": "🕌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1541432901042-2d8bd64b4a9b?w=1200&h=600&fit=crop&q=80"},
    {"name": "محراب فاخر", "price": 9500, "description": "", "emoji": "🕋", "type": "BANNER", "data": "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?w=1200&h=600&fit=crop&q=80"},
    {"name": "نقوش عربية", "price": 9000, "description": "", "emoji": "🎨", "type": "BANNER", "data": "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=1200&h=600&fit=crop&q=80"},
    {"name": "مسجد تاريخي", "price": 10500, "description": "", "emoji": "🕌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=1200&h=600&fit=crop&q=80"},
    {"name": "مآذن عالية", "price": 10000, "description": "", "emoji": "🕌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&h=600&fit=crop&q=80"},
    {"name": "مخطوطة قرآنية", "price": 9500, "description": "", "emoji": "📖", "type": "BANNER", "data": "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?w=1200&h=600&fit=crop&q=80"},
    {"name": "ساحة الحرم", "price": 12000, "description": "", "emoji": "🕋", "type": "BANNER", "data": "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?w=1200&h=600&fit=crop&q=80"},
    {"name": "أجواء رمضانية", "price": 10500, "description": "", "emoji": "🌙", "type": "BANNER", "data": "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?w=1200&h=600&fit=crop&q=80"},
    {"name": "سبحة فاخرة", "price": 8500, "description": "", "emoji": "📿", "type": "BANNER", "data": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=1200&h=600&fit=crop&q=80"},
    {"name": "قصر أندلسي", "price": 11000, "description": "", "emoji": "🏛️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&h=600&fit=crop&q=80"},
    {"name": "هلال متلألئ", "price": 9000, "description": "", "emoji": "🌙", "type": "BANNER", "data": "https://images.unsplash.com/photo-1532693322450-2cb5c511067d?w=1200&h=600&fit=crop&q=80"},
    {"name": "سجادة فاخرة", "price": 11500, "description": "", "emoji": "🌿", "type": "BANNER", "data": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=1200&h=600&fit=crop&q=80"},

    # --- 4. NATURAL PHENOMENA BANNERS (15 Banners) ---
    {"name": "صاعقة قوية", "price": 12000, "description": "", "emoji": "⚡", "type": "BANNER", "data": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1200&h=600&fit=crop&q=80"},
    {"name": "حمم بركانية", "price": 13000, "description": "", "emoji": "🌋", "type": "BANNER", "data": "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=1200&h=600&fit=crop&q=80"},
    {"name": "موجة هادرة", "price": 13500, "description": "", "emoji": "🌊", "type": "BANNER", "data": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1200&h=600&fit=crop&q=80"},
    {"name": "إعصار قمعي", "price": 13000, "description": "", "emoji": "🌪️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1527482797697-8795b05813fe?w=1200&h=600&fit=crop&q=80"},
    {"name": "عاصفة ترابية", "price": 11500, "description": "", "emoji": "🏜️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=1200&h=600&fit=crop&q=80"},
    {"name": "أورورا شمالية", "price": 12500, "description": "", "emoji": "🌌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=1200&h=600&fit=crop&q=80"},
    {"name": "هزات أرضية", "price": 14000, "description": "", "emoji": "⚡", "type": "BANNER", "data": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=1200&h=600&fit=crop&q=80"},
    {"name": "فيضان عارم", "price": 12500, "description": "", "emoji": "🌊", "type": "BANNER", "data": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1200&h=600&fit=crop&q=80"},
    {"name": "برق ليل", "price": 12000, "description": "", "emoji": "⚡", "type": "BANNER", "data": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=1200&h=600&fit=crop&q=80"},
    {"name": "كرة نار", "price": 13500, "description": "", "emoji": "☄️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=1200&h=600&fit=crop&q=80"},
    {"name": "فوهة بركان", "price": 13500, "description": "", "emoji": "🌋", "type": "BANNER", "data": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&h=600&fit=crop&q=80"},
    {"name": "أمواج عملاقة", "price": 12000, "description": "", "emoji": "🌊", "type": "BANNER", "data": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1200&h=600&fit=crop&q=80"},
    {"name": "عاصفة جليدية", "price": 11500, "description": "", "emoji": "❄️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&h=600&fit=crop&q=80"},
    {"name": "دوامة مائية", "price": 13000, "description": "", "emoji": "🌀", "type": "BANNER", "data": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1200&h=600&fit=crop&q=80"},
    {"name": "نيزك عابر", "price": 14000, "description": "", "emoji": "🌠", "type": "BANNER", "data": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1200&h=600&fit=crop&q=80"}
]

class ShopRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def seed_default_banner_products(self):
        """Deletes obsolete banners and seeds the exact 60 concise landscape banners"""
        default_names = {b["name"] for b in DEFAULT_BANNERS}
        
        # Remove old banner products not in default list
        stmt = select(ShopProduct).where(ShopProduct.type == "BANNER")
        res = await self.session.execute(stmt)
        existing_banners = res.scalars().all()
        for eb in existing_banners:
            if eb.name not in default_names:
                await self.session.delete(eb)

        for banner in DEFAULT_BANNERS:
            stmt = select(ShopProduct).where(ShopProduct.name == banner["name"])
            res = await self.session.execute(stmt)
            existing = res.scalar_one_or_none()
            if not existing:
                p = ShopProduct(
                    name=banner["name"],
                    price=banner["price"],
                    description="",
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
            else:
                existing.data = banner["data"]
                existing.price = banner["price"]
                existing.description = ""
                existing.emoji = banner["emoji"]
                existing.updated_at = utc_now()
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
