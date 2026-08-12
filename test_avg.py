import asyncio
from bot.database.connection import AsyncSessionLocal
from sqlalchemy import select, func
from bot.database.models.economy import Wallet

async def main():
    async with AsyncSessionLocal() as session:
        col = Wallet.balance + Wallet.bank_balance
        stmt = select(func.count(Wallet.user_id), func.coalesce(func.sum(col), 0)).where(col > 0)
        res = await session.execute(stmt)
        count, total = res.one()
        print(count, total)

asyncio.run(main())
