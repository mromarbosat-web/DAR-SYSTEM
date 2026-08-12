import asyncio
from bot.database.connection import AsyncSessionLocal
from bot.database.repositories.shop_repository import ShopRepository
from bot.database.models.economy import ShopProduct, Wallet, UserInventory, Transaction
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        # Create a wallet
        wallet = Wallet(user_id=123, balance=100)
        session.add(wallet)
        
        # Create a product
        product = ShopProduct(name="Test", price=10)
        session.add(product)
        await session.commit()

        # Buy product
        repo = ShopRepository(session)
        success, msg, prod = await repo.purchase_product_atomic(123, product.product_id)
        print("Buy Success:", success)

        # Check balance
        stmt = select(Wallet).where(Wallet.user_id == 123)
        w = (await session.execute(stmt)).scalar_one()
        print("Balance after:", w.balance)

asyncio.run(main())
