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
    {"name": "غابة خضراء", "price": 8000, "description": "", "emoji": "🌲", "type": "BANNER", "data": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200&h=600&fit=crop&q=80"},
    {"name": "شروق شمس", "price": 8500, "description": "", "emoji": "🌅", "type": "BANNER", "data": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&h=600&fit=crop&q=80"},
    {"name": "بحيرة هادئة", "price": 9000, "description": "", "emoji": "🏞️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&h=600&fit=crop&q=80"},
    {"name": "حقول ذهبية", "price": 7500, "description": "", "emoji": "🌾", "type": "BANNER", "data": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1200&h=600&fit=crop&q=80"},
    {"name": "أزهار ربيع", "price": 7000, "description": "", "emoji": "🌸", "type": "BANNER", "data": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1200&h=600&fit=crop&q=80"},
    {"name": "قمم ثلجية", "price": 9500, "description": "", "emoji": "🏔️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&h=600&fit=crop&q=80"},
    {"name": "شلال منساب", "price": 9000, "description": "", "emoji": "🌊", "type": "BANNER", "data": "https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?w=1200&h=600&fit=crop&q=80"},
    {"name": "جزيرة استوائية", "price": 10000, "description": "", "emoji": "🏝️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&h=600&fit=crop&q=80"},
    {"name": "سماء صافية", "price": 7500, "description": "", "emoji": "⛅", "type": "BANNER", "data": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1200&h=600&fit=crop&q=80"},
    {"name": "واحة خضراء", "price": 8000, "description": "", "emoji": "🌴", "type": "BANNER", "data": "https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=1200&h=600&fit=crop&q=80"},
    {"name": "غروب دافئ", "price": 8500, "description": "", "emoji": "🌇", "type": "BANNER", "data": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&h=600&fit=crop&q=80"},
    {"name": "أوراق خريف", "price": 7500, "description": "", "emoji": "🍂", "type": "BANNER", "data": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&h=600&fit=crop&q=80"},
    {"name": "أفق مضيء", "price": 9000, "description": "", "emoji": "🏙️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1200&h=600&fit=crop&q=80"},
    {"name": "طبيعة بكر", "price": 8500, "description": "", "emoji": "🌿", "type": "BANNER", "data": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200&h=600&fit=crop&q=80"},
    {"name": "سحب بيضاء", "price": 8000, "description": "", "emoji": "☁️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1200&h=600&fit=crop&q=80"},

    # --- 2. DARK & MYSTERIOUS BANNERS (15 Banners) ---
    {"name": "فضاء كوني", "price": 11000, "description": "", "emoji": "🌌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1200&h=600&fit=crop&q=80"},
    {"name": "سايبر نيون", "price": 12000, "description": "", "emoji": "⚡", "type": "BANNER", "data": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1200&h=600&fit=crop&q=80"},
    {"name": "قمر دموي", "price": 13000, "description": "", "emoji": "🌑", "type": "BANNER", "data": "https://images.unsplash.com/photo-1532693322450-2cb5c511067d?w=1200&h=600&fit=crop&q=80"},
    {"name": "كهف مظلم", "price": 10500, "description": "", "emoji": "🦇", "type": "BANNER", "data": "https://images.unsplash.com/photo-1519751138087-5bf79df62d5b?w=1200&h=600&fit=crop&q=80"},
    {"name": "سديم غامض", "price": 12500, "description": "", "emoji": "✨", "type": "BANNER", "data": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&h=600&fit=crop&q=80"},
    {"name": "ليال مظلمة", "price": 11000, "description": "", "emoji": "🌙", "type": "BANNER", "data": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1200&h=600&fit=crop&q=80"},
    {"name": "ظلال عميقة", "price": 11500, "description": "", "emoji": "👤", "type": "BANNER", "data": "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=1200&h=600&fit=crop&q=80"},
    {"name": "غابة معتمة", "price": 10000, "description": "", "emoji": "🌲", "type": "BANNER", "data": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200&h=600&fit=crop&q=80"},
    {"name": "ثقب أسود", "price": 15000, "description": "", "emoji": "🕳️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1502134249126-9f3755a50d78?w=1200&h=600&fit=crop&q=80"},
    {"name": "أطياف خفية", "price": 12000, "description": "", "emoji": "👻", "type": "BANNER", "data": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1200&h=600&fit=crop&q=80"},
    {"name": "عالم مجهول", "price": 13500, "description": "", "emoji": "🔮", "type": "BANNER", "data": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=1200&h=600&fit=crop&q=80"},
    {"name": "مدينة مظلمة", "price": 11000, "description": "", "emoji": "🌃", "type": "BANNER", "data": "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=1200&h=600&fit=crop&q=80"},
    {"name": "نيزك مهلك", "price": 14000, "description": "", "emoji": "☄️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1200&h=600&fit=crop&q=80"},
    {"name": "بحر أسود", "price": 11500, "description": "", "emoji": "🌊", "type": "BANNER", "data": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1200&h=600&fit=crop&q=80"},
    {"name": "طاقة سوداء", "price": 14500, "description": "", "emoji": "🖤", "type": "BANNER", "data": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200&h=600&fit=crop&q=80"},

    # --- 3. ISLAMIC BANNERS (Mosques & Prayer Rugs - 15 Banners) ---
    {"name": "سجادة صلاة", "price": 9000, "description": "", "emoji": "🕌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=1200&h=600&fit=crop&q=80"},
    {"name": "مسجد تاريخي", "price": 10000, "description": "", "emoji": "🕌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?w=1200&h=600&fit=crop&q=80"},
    {"name": "فانوس رمضان", "price": 8500, "description": "", "emoji": "✨", "type": "BANNER", "data": "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?w=1200&h=600&fit=crop&q=80"},
    {"name": "قبة ذهبية", "price": 11000, "description": "", "emoji": "🕌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&h=600&fit=crop&q=80"},
    {"name": "محراب خشوع", "price": 9500, "description": "", "emoji": "🕋", "type": "BANNER", "data": "https://images.unsplash.com/photo-1541432901042-2d8bd64b4a9b?w=1200&h=600&fit=crop&q=80"},
    {"name": "زخارف إسلامية", "price": 9000, "description": "", "emoji": "🎨", "type": "BANNER", "data": "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=1200&h=600&fit=crop&q=80"},
    {"name": "مسجد أزرق", "price": 10500, "description": "", "emoji": "🕌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=1200&h=600&fit=crop&q=80"},
    {"name": "مئذنة شامخة", "price": 10000, "description": "", "emoji": "🕌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?w=1200&h=600&fit=crop&q=80"},
    {"name": "مصحف كريم", "price": 9500, "description": "", "emoji": "📖", "type": "BANNER", "data": "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?w=1200&h=600&fit=crop&q=80"},
    {"name": "سكينة الحرم", "price": 12000, "description": "", "emoji": "🕋", "type": "BANNER", "data": "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&h=600&fit=crop&q=80"},
    {"name": "صلاة ليلية", "price": 10500, "description": "", "emoji": "🌙", "type": "BANNER", "data": "https://images.unsplash.com/photo-1541432901042-2d8bd64b4a9b?w=1200&h=600&fit=crop&q=80"},
    {"name": "تسبيح وذكر", "price": 8500, "description": "", "emoji": "📿", "type": "BANNER", "data": "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=1200&h=600&fit=crop&q=80"},
    {"name": "عمارة إسلامية", "price": 11000, "description": "", "emoji": "🏛️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=1200&h=600&fit=crop&q=80"},
    {"name": "هلال رمضان", "price": 9000, "description": "", "emoji": "🌙", "type": "BANNER", "data": "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?w=1200&h=600&fit=crop&q=80"},
    {"name": "روضة مباركة", "price": 11500, "description": "", "emoji": "🌿", "type": "BANNER", "data": "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?w=1200&h=600&fit=crop&q=80"},

    # --- 4. NATURAL PHENOMENA BANNERS (15 Banners) ---
    {"name": "برق رعد", "price": 12000, "description": "", "emoji": "⚡", "type": "BANNER", "data": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=1200&h=600&fit=crop&q=80"},
    {"name": "حمم بركانية", "price": 13000, "description": "", "emoji": "🌋", "type": "BANNER", "data": "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=1200&h=600&fit=crop&q=80"},
    {"name": "تسونامي جارف", "price": 13500, "description": "", "emoji": "🌊", "type": "BANNER", "data": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1200&h=600&fit=crop&q=80"},
    {"name": "إعصار مدمر", "price": 13000, "description": "", "emoji": "🌪️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1527482797697-8795b05813fe?w=1200&h=600&fit=crop&q=80"},
    {"name": "عاصفة رملية", "price": 11500, "description": "", "emoji": "🏜️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=1200&h=600&fit=crop&q=80"},
    {"name": "شفق قطبي", "price": 12500, "description": "", "emoji": "🌌", "type": "BANNER", "data": "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=1200&h=600&fit=crop&q=80"},
    {"name": "زلزال عنيف", "price": 14000, "description": "", "emoji": "⚡", "type": "BANNER", "data": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=1200&h=600&fit=crop&q=80"},
    {"name": "فيضانات عارمة", "price": 12500, "description": "", "emoji": "🌊", "type": "BANNER", "data": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1200&h=600&fit=crop&q=80"},
    {"name": "صواعق ليلية", "price": 12000, "description": "", "emoji": "⚡", "type": "BANNER", "data": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1200&h=600&fit=crop&q=80"},
    {"name": "نيزك متوهج", "price": 13500, "description": "", "emoji": "☄️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1200&h=600&fit=crop&q=80"},
    {"name": "بركان غاضب", "price": 13500, "description": "", "emoji": "🌋", "type": "BANNER", "data": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&h=600&fit=crop&q=80"},
    {"name": "أمواج عاتية", "price": 12000, "description": "", "emoji": "🌊", "type": "BANNER", "data": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1200&h=600&fit=crop&q=80"},
    {"name": "عاصفة ثلجية", "price": 11500, "description": "", "emoji": "❄️", "type": "BANNER", "data": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&h=600&fit=crop&q=80"},
    {"name": "دوامة بحرية", "price": 13000, "description": "", "emoji": "🌀", "type": "BANNER", "data": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1200&h=600&fit=crop&q=80"},
    {"name": "نيزك فضي", "price": 14000, "description": "", "emoji": "🌠", "type": "BANNER", "data": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1200&h=600&fit=crop&q=80"}
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
