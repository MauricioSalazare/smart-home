import logging
from logging.handlers import RotatingFileHandler
import functools
from pathlib import Path


import sys

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

def setup_logger(name: str,
                 log_file: str = 'smart-meter.log',
                 max_bytes: int = 5_000_000,
                 backup_count: int =5) -> logging.Logger:

    logger = logging.getLogger(name)
    logger.setLevel("INFO")
    logger.handlers.clear()

    prd_format = "%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d] %(message)s"

    formatter = logging.Formatter(fmt=prd_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (rotating)
    log_path = LOG_DIR / log_file
    file_handler = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def log_function_call(func, logger):
    """
    Decorator to automatically log function calls.
    Logs when the function starts and finishes.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Calling function: {func.__name__}")
        result = func(*args, **kwargs)
        logger.info(f"Function {func.__name__} finished execution")
        return result
    return wrapper