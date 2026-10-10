"""
logging_config.py - Safe logging configuration for VERONICA.
Ensures sensitive tokens and keys are never printed to logs.
"""

import logging
import re
from config.settings import settings


class SafeFormatter(logging.Formatter):
    """A log formatter that masks potential sensitive keys and tokens."""

    SENSITIVE_PATTERNS = [
        re.compile(r"gsk_[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
        re.compile(r"(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?", re.IGNORECASE),
    ]

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for pattern in self.SENSITIVE_PATTERNS:
            message = pattern.sub("[REDACTED]", message)
        return message


def setup_logger(name: str = "VERONICA") -> logging.Logger:
    """Configures and returns a safe logger instance."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = SafeFormatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
