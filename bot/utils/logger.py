import logging
import sys
from bot.config.settings import settings

def setup_logger():
    logger = logging.getLogger("discord_bot")
    logger.setLevel(settings.LOG_LEVEL.upper())

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger

logger = setup_logger()
