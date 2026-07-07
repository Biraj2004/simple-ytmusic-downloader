import logging
from logging.handlers import RotatingFileHandler
from utils.paths import LOGS_DIR

# Configure rotating file handler for rolling logs
log_file = LOGS_DIR / "app.log"
logger = logging.getLogger("YTMusicDownloader")
logger.setLevel(logging.DEBUG)

# Prevents double logs if imported multiple times
if not logger.handlers:
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Max 2MB, 1 backup (app.log.1)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=2 * 1024 * 1024,
        backupCount=1,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Console handler for debugging during development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

def get_logger():
    return logger
