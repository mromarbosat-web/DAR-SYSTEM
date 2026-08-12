import asyncio
from bot.database.connection import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        queries = [
            "ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS voice_log_channel_id BIGINT;",
            "ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS invite_log_channel_id BIGINT;",
            "ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS economy_log_channel_id BIGINT;",
            "ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS verification_log_channel_id BIGINT;",
            "ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS automod_log_channel_id BIGINT;"
        ]
        for q in queries:
            await session.execute(text(q))
        await session.commit()

asyncio.run(main())
