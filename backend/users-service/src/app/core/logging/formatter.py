# app/core/logging/formatters.py
import json
import logging
from datetime import datetime
from app.core.logging.context import request_id_ctx, user_id_ctx

class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
            "user_id": user_id_ctx.get(),
        }

        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra"):
            log.update(record.extra)

        return json.dumps(log, ensure_ascii=False)
