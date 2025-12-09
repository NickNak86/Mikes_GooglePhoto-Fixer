# utils/logging_config.py
"""
Small logging helper for GooglePhoto-Fixer.

Usage:
  from utils.logging_config import configure_logging
  configure_logging(log_path="logs/photo_fixer.log", level="INFO")
"""
import logging
import os
from logging.handlers import RotatingFileHandler

def configure_logging(log_path="logs/photo_fixer.log", level="INFO", max_bytes=5*1024*1024, backup_count=3):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # File handler (rotating)
    fh = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    fh.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Avoid adding duplicate handlers on repeated imports
    if not any(isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", None) == os.path.abspath(log_path) for h in logger.handlers if hasattr(h, "baseFilename")):
        logger.addHandler(fh)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        logger.addHandler(ch)

    logging.getLogger(__name__).info("Logging configured, file=%s", log_path)
