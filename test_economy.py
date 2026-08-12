import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.connection import init_db, AsyncSessionLocal
from bot.database.repositories.economy_repository import EconomyRepository
from bot.database.repositories.shop_repository import ShopRepository
from bot.services.economy_service import EconomyService

async def test_economy():
    await init_db()
    async with AsyncSessionLocal() as session:
        repo = EconomyRepository(session)
        
        print("Testing Wallet...")
        wallet = await repo.get_or_create_wallet(user_id=111, for_update=True)
        print("Initial balance:", wallet.balance)
        
        print("Adding money...")
        success, b, a, tx = await repo.update_balance_atomic(111, 500, "TEST", 1)
        print(f"Added money. Success: {success}, Before: {b}, After: {a}")
        
        print("Fetching global average...")
        cnt, total, avg = await repo.get_global_average()
        print(f"Count: {cnt}, Total: {total}, Avg: {avg}")
        
        print("Testing EconomySettings...")
        es = await repo.get_economy_settings(1)
        print(f"Daily reward amount: {es.daily_reward_amount}")
        
        print("Testing Shop...")
        shop = ShopRepository(session)
        prod = await shop.create_product(name="Test Role", price=100, prod_type="ROLE", role_id=222)
        print(f"Created product: {prod.name} (ID: {prod.product_id})")
        
        prods = await shop.get_products()
        print(f"Total products: {len(prods)}")
        
        print("Purchasing product...")
        success, msg = await shop.purchase_product(user_id=111, product_id=prod.product_id)
        print(f"Purchase status: {success}, Message: {msg}")
        
        print("Final balance check...")
        w2 = await repo.get_or_create_wallet(user_id=111)
        print("Final balance:", w2.balance)
        
        # Rollback so we don't mess up the db
        await session.rollback()

asyncio.run(test_economy())
