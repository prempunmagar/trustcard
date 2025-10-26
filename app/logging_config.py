"""
Structured Logging Configuration

Provides JSON logging for production and human-readable logging for development.
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from logger.info(..., extra={...})
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add any custom attributes
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "extra_fields"
            ]:
                log_data[key] = value

        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for development"""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
        "RESET": "\033[0m"      # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        record.levelname = f"{color}{record.levelname}{reset}"

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Build log message
        message = f"{timestamp} | {record.levelname:<17} | {record.name:<30} | {record.getMessage()}"

        # Add exception info if present
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)

        return message


def setup_logging(
    log_level: str = "INFO",
    environment: str = "development",
    log_file: str = None
):
    """
    Setup logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        environment: Environment name (development, production)
        log_file: Optional log file path
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Use JSON formatter for production, colored for development
    if environment == "production":
        formatter = JSONFormatter()
    else:
        formatter = ColoredFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)

        # Always use JSON for file logs
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)
    logging.getLogger("instagrapi").setLevel(logging.WARNING)

    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized",
        extra={
            "environment": environment,
            "log_level": log_level,
            "log_file": log_file
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with extra field support

    Usage:
        logger = get_logger(__name__)
        logger.info("Message", extra={"user_id": 123, "action": "login"})
    """
    logger = logging.getLogger(name)

    # Wrap logger methods to support extra fields
    original_info = logger.info
    original_warning = logger.warning
    original_error = logger.error
    original_debug = logger.debug

    def _wrap_log_method(original_method):
        def wrapper(msg, *args, extra=None, **kwargs):
            if extra:
                # Store extra fields in a special attribute
                record = logging.LogRecord(
                    name=logger.name,
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=msg,
                    args=args,
                    exc_info=None
                )
                record.extra_fields = extra
            return original_method(msg, *args, extra=extra, **kwargs)
        return wrapper

    logger.info = _wrap_log_method(original_info)
    logger.warning = _wrap_log_method(original_warning)
    logger.error = _wrap_log_method(original_error)
    logger.debug = _wrap_log_method(original_debug)

    return logger


# Request logging middleware helper
class RequestLogger:
    """Helper for logging HTTP requests"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_ip: str = None
    ):
        """Log HTTP request"""
        self.logger.info(
            f"{method} {path} - {status_code} ({duration_ms:.2f}ms)",
            extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip
            }
        )

    def log_error(
        self,
        method: str,
        path: str,
        error: str,
        client_ip: str = None
    ):
        """Log HTTP error"""
        self.logger.error(
            f"{method} {path} - Error: {error}",
            extra={
                "method": method,
                "path": path,
                "error": error,
                "client_ip": client_ip
            }
        )
