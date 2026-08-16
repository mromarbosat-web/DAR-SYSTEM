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

async def migrate_command_shortcuts_columns():
    """Adds ignored_roles and other missing columns to command_shortcuts table safely without dropping or losing data."""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("Checking and running migrations for command_shortcuts table...")
            # 1. Create table if not exists
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS command_shortcuts (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL REFERENCES guilds(guild_id) ON DELETE CASCADE,
                    trigger_word VARCHAR(100) NOT NULL,
                    target_action VARCHAR(50) NOT NULL,
                    allowed_roles VARCHAR(500),
                    ignored_roles VARCHAR(500),
                    allowed_users VARCHAR(500),
                    allowed_channels VARCHAR(500),
                    ignored_channels VARCHAR(500),
                    enabled BOOLEAN DEFAULT TRUE NOT NULL,
                    created_by BIGINT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_guild_trigger_word UNIQUE (guild_id, trigger_word)
                );
            """))

            # 2. Add missing columns safely if the table already existed with older schema
            columns_to_ensure = [
                ("ignored_roles", "VARCHAR(500)"),
                ("allowed_roles", "VARCHAR(500)"),
                ("allowed_channels", "VARCHAR(500)"),
                ("ignored_channels", "VARCHAR(500)"),
                ("allowed_users", "VARCHAR(500)"),
                ("enabled", "BOOLEAN DEFAULT TRUE"),
                ("target_action", "VARCHAR(50)"),
                ("trigger_word", "VARCHAR(100)"),
                ("created_by", "BIGINT"),
                ("created_at", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"),
                ("updated_at", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
            ]

            for col_name, col_type in columns_to_ensure:
                try:
                    await session.execute(text(f"ALTER TABLE command_shortcuts ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                except Exception as col_err:
                    logger.debug(f"Column check for command_shortcuts.{col_name}: {col_err}")

            # 3. Ensure indexes exist
            try:
                await session.execute(text("CREATE INDEX IF NOT EXISTS idx_shortcuts_guild ON command_shortcuts(guild_id);"))
                await session.execute(text("CREATE INDEX IF NOT EXISTS idx_shortcuts_trigger ON command_shortcuts(trigger_word);"))
            except Exception as idx_err:
                logger.debug(f"Index check for command_shortcuts: {idx_err}")

            await session.commit()
            logger.info("Successfully completed command_shortcuts database migration.")
        except Exception as e:
            await session.rollback()
            logger.error(f"command_shortcuts migration failed: {e}")
            raise e

async def migrate_member_activity_table():
    """Creates the member_activity table and necessary composite indexes if they do not exist."""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("Checking and creating member_activity table if not exists...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS member_activity (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    activity_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    messages_count INTEGER NOT NULL DEFAULT 0,
                    voice_seconds INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_member_activity_guild_user_date UNIQUE (guild_id, user_id, activity_date)
                );
            """))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_activity_guild_date ON member_activity(guild_id, activity_date);"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_activity_user ON member_activity(user_id);"))
            await session.commit()
            logger.info("Successfully completed member_activity migration.")
        except Exception as e:
            await session.rollback()
            logger.error(f"member_activity migration failed: {e}")
            raise e

async def migrate_user_profile_columns():
    """Adds bio_color and any missing columns to user_profiles table safely."""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("Checking and running migrations for user_profiles table...")
            await session.execute(text("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS bio_color VARCHAR(50) DEFAULT '#FFFFFF';"))
            await session.commit()
            logger.info("Successfully checked/added bio_color column to user_profiles.")
        except Exception as e:
            await session.rollback()
            logger.error(f"user_profiles migration error: {e}")

async def run_migrations():
    """Runs all necessary database migrations."""
    logger.info("Starting database migrations...")
    await add_local_id_column()
    await migrate_command_shortcuts_columns()
    await migrate_member_activity_table()
    await migrate_user_profile_columns()
    logger.info("All migrations completed successfully.")

if __name__ == "__main__":
    asyncio.run(run_migrations())
