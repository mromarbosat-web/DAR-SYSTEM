import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    )
    
    # Format connection string for asyncpg if postgresql:// is provided
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEFAULT_PREFIX: str = os.getenv("BOT_PREFIX", "!")
    DEFAULT_EMBED_COLOR: int = int(os.getenv("DEFAULT_EMBED_COLOR", "0x5865F2"), 16)
    
    # Security Colors
    COLOR_SUCCESS: int = 0x57F287  # Green
    COLOR_ERROR: int = 0xED4245    # Red
    COLOR_WARNING: int = 0xFEE75C  # Yellow
    COLOR_INFO: int = 0x5865F2     # Blurple
    COLOR_SECURITY: int = 0xEB459E # Fuchsia

settings = Settings()
