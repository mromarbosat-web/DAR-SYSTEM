import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
    
    # Bot Owners & Main Guild Configuration
    BOT_OWNER_IDS_RAW: str = os.getenv("BOT_OWNER_IDS", "1406547827865288786,1377224857292636200")
    MAIN_GUILD_ID: int = int(os.getenv("MAIN_GUILD_ID", "1391459645528215582"))
    CURRENCY_NAME: str = os.getenv("CURRENCY_NAME", "سراب")
    CURRENCY_EMOJI: str = os.getenv("CURRENCY_EMOJI", "🌫️")

    @property
    def BOT_OWNER_IDS(self) -> set[int]:
        ids = set()
        for raw in self.BOT_OWNER_IDS_RAW.replace(",", " ").split():
            raw = raw.strip()
            if raw.isdigit():
                ids.add(int(raw))
        # Ensure default Bot Owners are always present if configured
        ids.add(1406547827865288786)
        ids.add(1377224857292636200)
        return ids

    def is_bot_owner(self, user_id: int) -> bool:
        return user_id in self.BOT_OWNER_IDS

    # Security Colors
    COLOR_SUCCESS: int = 0x57F287  # Green
    COLOR_ERROR: int = 0xED4245    # Red
    COLOR_WARNING: int = 0xFEE75C  # Yellow
    COLOR_INFO: int = 0x5865F2     # Blurple
    COLOR_SECURITY: int = 0xEB459E # Fuchsia

settings = Settings()
