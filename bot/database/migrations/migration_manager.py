import asyncio
from sqlalchemy import text
from bot.database.connection import AsyncSessionLocal
from bot.utils.logger import logger

async def add_local_id_column():
    """Adds local_id column to warnings table if it doesn't exist and populates it."""
    async with AsyncSessionLocal() as session:
        try:
            # 1. Check if column exists
            result = await session.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='warnings' AND column_name='local_id';"
            ))
            column_exists = result.scalar()
            
            if not column_exists:
                logger.info("Adding local_id column to warnings table...")
                # 2. Add column
                await session.execute(text("ALTER TABLE warnings ADD COLUMN local_id INTEGER DEFAULT 1;"))
                await session.commit()
                logger.info("Successfully added local_id column.")
            else:
                logger.info("local_id column already exists in warnings table.")

            # 3. Populate local_id for existing records if they have defaults (all 1s) or are null
            # This logic assigns sequential IDs per guild/user for existing warnings
            logger.info("Verifying and populating local_id values for existing warnings...")
            
            # Get guilds and users with warnings
            result = await session.execute(text("SELECT DISTINCT guild_id, user_id FROM warnings;"))
            user_guilds = result.all()
            
            for guild_id, user_id in user_guilds:
                # Get all warnings for this user in this guild ordered by creation
                warnings_res = await session.execute(text(
                    "SELECT warning_id FROM warnings "
                    "WHERE guild_id = :guild_id AND user_id = :user_id "
                    "ORDER BY created_at ASC;"
                ), {"guild_id": guild_id, "user_id": user_id})
                
                warning_ids = [r[0] for r in warnings_res.all()]
                
                for idx, warning_id in enumerate(warning_ids, start=1):
                    await session.execute(text(
                        "UPDATE warnings SET local_id = :local_id "
                        "WHERE warning_id = :warning_id;"
                    ), {"local_id": idx, "warning_id": warning_id})
            
            await session.commit()
            logger.info("Successfully populated local_id for all existing warnings.")

        except Exception as e:
            await session.rollback()
            logger.error(f"Migration failed: {e}")
            raise e

async def run_migrations():
    """Runs all necessary database migrations."""
    logger.info("Starting database migrations...")
    await add_local_id_column()
    logger.info("All migrations completed successfully.")

if __name__ == "__main__":
    asyncio.run(run_migrations())
