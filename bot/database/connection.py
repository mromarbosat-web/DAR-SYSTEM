import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from bot.config.settings import settings

logger = logging.getLogger("discord_bot.database")

# Base class for SQLAlchemy ORM models
class Base(DeclarativeBase):
    pass

# Create Engine with Supabase connection pooling support
engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    connect_args={
        "server_settings": {
            "application_name": "Discord_Security_Bot"
        },
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0
    }
)

# Create sessionmaker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        try:
            async with engine.begin() as conn:
                from sqlalchemy import text
                await conn.execute(text("ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS voice_log_channel_id BIGINT;"))
                await conn.execute(text("ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS invite_log_channel_id BIGINT;"))
                await conn.execute(text("ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS economy_log_channel_id BIGINT;"))
                await conn.execute(text("ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS verification_log_channel_id BIGINT;"))
                await conn.execute(text("ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS automod_log_channel_id BIGINT;"))
                
                # Command shortcuts schema patch
                await conn.execute(text("ALTER TABLE command_shortcuts ADD COLUMN IF NOT EXISTS ignored_roles VARCHAR(500);"))
                await conn.execute(text("ALTER TABLE command_shortcuts ADD COLUMN IF NOT EXISTS allowed_roles VARCHAR(500);"))
                await conn.execute(text("ALTER TABLE command_shortcuts ADD COLUMN IF NOT EXISTS allowed_channels VARCHAR(500);"))
                await conn.execute(text("ALTER TABLE command_shortcuts ADD COLUMN IF NOT EXISTS ignored_channels VARCHAR(500);"))
                await conn.execute(text("ALTER TABLE command_shortcuts ADD COLUMN IF NOT EXISTS allowed_users VARCHAR(500);"))
                await conn.execute(text("ALTER TABLE command_shortcuts ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT TRUE;"))
        except Exception as e:
            logger.warning(f"Error patching db {e}")

        logger.info("Database tables initialized successfully via SQLAlchemy Base metadata.")
    except Exception as e:
        logger.error(f"Error initializing database schema: {e}", exc_info=True)
        raise e

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency helper for database session yielding"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
