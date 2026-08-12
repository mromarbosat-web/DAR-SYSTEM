import re

with open("bot/database/connection.py", "r") as f:
    content = f.read()

patch = """
        try:
            async with engine.begin() as conn:
                from sqlalchemy import text
                await conn.execute(text("ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS voice_log_channel_id BIGINT;"))
                await conn.execute(text("ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS invite_log_channel_id BIGINT;"))
                await conn.execute(text("ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS economy_log_channel_id BIGINT;"))
                await conn.execute(text("ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS verification_log_channel_id BIGINT;"))
                await conn.execute(text("ALTER TABLE log_settings ADD COLUMN IF NOT EXISTS automod_log_channel_id BIGINT;"))
        except Exception as e:
            logger.warning(f"Error patching db {e}")
"""

content = content.replace("await conn.run_sync(Base.metadata.create_all)", "await conn.run_sync(Base.metadata.create_all)" + patch)

with open("bot/database/connection.py", "w") as f:
    f.write(content)
