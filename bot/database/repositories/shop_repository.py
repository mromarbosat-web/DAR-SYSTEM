import logging
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.economy import ShopProduct, UserInventory, Wallet, Transaction

logger = logging.getLogger("discord_bot.shop_repository")

class ShopRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

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
            enabled=enabled
        )
        self.session.add(product)
        await self.session.flush()
        return product

    async def update_product(self, product_id: int, **kwargs) -> Optional[ShopProduct]:
        product = await self.get_product(product_id)
        if not product:
            return None

        for key, val in kwargs.items():
            if hasattr(product, key) and val is not None:
                setattr(product, key, val)
        product.updated_at = datetime.utcnow()
        await self.session.flush()
        return product

    async def delete_product(self, product_id: int) -> bool:
        stmt = delete(ShopProduct).where(ShopProduct.product_id == product_id)
        res = await self.session.execute(stmt)
        return res.rowcount > 0

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
        async with self.session.begin_nested():
            # Lock product and wallet
            stmt_p = select(ShopProduct).where(ShopProduct.product_id == product_id).with_for_update()
            res_p = await self.session.execute(stmt_p)
            product = res_p.scalar_one_or_none()

            if not product or not product.enabled:
                return False, "هذا المنتج غير متاح في المتجر حاليًا!", None

            if product.stock == 0:
                return False, "عذرًا، نفد مخزون هذا المنتج بالكامل!", product

            # Check max per user
            current_qty = await self.get_user_item_count(user_id, product_id)
            if product.max_per_user > 0 and current_qty >= product.max_per_user:
                return False, f"لقد وصلت للحد الأقصى المسموح بشرائه لهذا المنتج (`{product.max_per_user}` قطعة)!", product

            # Check wallet
            stmt_w = select(Wallet).where(Wallet.user_id == user_id).with_for_update()
            res_w = await self.session.execute(stmt_w)
            wallet = res_w.scalar_one_or_none()

            if not wallet or wallet.balance < product.price:
                curr_bal = wallet.balance if wallet else 0
                return False, f"رصيدك الحالي (`{curr_bal}` سراب) غير كافٍ لشراء هذا المنتج (`{product.price}` سراب)!", product

            # Deduct wallet
            b_before = wallet.balance
            wallet.balance -= product.price
            wallet.updated_at = datetime.utcnow()

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
                inv_item.updated_at = datetime.utcnow()
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
            await self.session.flush()

            return True, f"تم شراء `{product.name}` بنجاح بسعر `{product.price}` سراب!", product
