# app/core/logging/logger.py
import logging
import logging.config
from app.core.logging.formatter import JsonLogFormatter

def setup_logging(level: str = "INFO") -> None:
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JsonLogFormatter,
            }
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "json",
            }
        },
        "root": {
            "level": level,
            "handlers": ["default"],
        },
    }

    logging.config.dictConfig(logging_config)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
