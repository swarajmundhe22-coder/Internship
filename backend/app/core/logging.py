import json
import logging
import sys
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any, Dict

# Security Hardened: Fallback to standard JSON formatting if pythonjsonlogger is missing.
try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False


_CORRELATION_ID_VAR: ContextVar[str] = ContextVar("gifip_correlation_id", default="system")


def set_correlation_id(correlation_id: str) -> Token:
    return _CORRELATION_ID_VAR.set(correlation_id)


def reset_correlation_id(token: Token) -> None:
    _CORRELATION_ID_VAR.reset(token)


def get_correlation_id() -> str:
    return _CORRELATION_ID_VAR.get()

class StructuredJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
        }
        correlation_id = getattr(record, 'correlation_id', get_correlation_id())
        log_record['correlation_id'] = correlation_id
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging(level: str = "INFO") -> None:
    logger = logging.getLogger()
    logger.setLevel(level.upper())

    if getattr(logger, "_gifip_logging_configured", False):
        return

    log_handler = logging.StreamHandler(sys.stdout)
    
    if HAS_JSON_LOGGER:
        # Re-using the logic if the package exists
        class CustomJsonFormatter(jsonlogger.JsonFormatter):
            def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
                super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
                if not log_record.get('timestamp'):
                    log_record['timestamp'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                log_record['level'] = log_record.get('level', record.levelname).upper()
                log_record['correlation_id'] = getattr(record, 'correlation_id', get_correlation_id())

        formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    else:
        formatter = StructuredJsonFormatter()

    log_handler.setFormatter(formatter)
    logger.handlers = [log_handler]
    logger.addFilter(CorrelationIdFilter())

    # Suppress verbose third-party logs
    logging.getLogger("uvicorn.access").handlers = [log_handler]
    logging.getLogger("uvicorn.error").handlers = [log_handler]
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logger._gifip_logging_configured = True  # type: ignore[attr-defined]

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = get_correlation_id()
        return True
