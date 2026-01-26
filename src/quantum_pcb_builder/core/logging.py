"""Logging configuration for the Quantum PCB Builder system.

This module provides standardized logging configuration with support for
structured logging, log levels, and output formatting.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class LogLevel(Enum):
    """Log level enumeration."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "taskName",
            }:
                log_data[key] = value

        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """Formatter for human-readable console output with colors."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, "")
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        formatted = (
            f"{color}[{timestamp}] [{record.levelname:8}] "
            f"{record.name}: {record.getMessage()}{self.RESET}"
        )

        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


class LoggerFactory:
    """Factory for creating configured loggers."""

    _configured: bool = False
    _default_level: int = logging.INFO
    _use_structured: bool = False

    @classmethod
    def configure(
        cls,
        level: LogLevel = LogLevel.INFO,
        structured: bool = False,
        log_file: str | None = None,
    ) -> None:
        """Configure global logging settings.

        Args:
            level: The minimum log level.
            structured: Whether to use JSON structured logging.
            log_file: Optional file path for file logging.
        """
        cls._default_level = level.value
        cls._use_structured = structured

        # Configure root logger
        root_logger = logging.getLogger("quantum_pcb_builder")
        root_logger.setLevel(cls._default_level)

        # Remove existing handlers
        root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(cls._default_level)

        if structured:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(ConsoleFormatter())

        root_logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(cls._default_level)
            file_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(file_handler)

        cls._configured = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger with the specified name.

        Args:
            name: The logger name (typically __name__).

        Returns:
            Configured logger instance.
        """
        if not cls._configured:
            cls.configure()

        logger = logging.getLogger(f"quantum_pcb_builder.{name}")
        return logger


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger.

    Args:
        name: The logger name.

    Returns:
        Configured logger instance.
    """
    return LoggerFactory.get_logger(name)


class LogContext:
    """Context manager for adding structured context to log messages."""

    def __init__(self, logger: logging.Logger, **context: Any) -> None:
        """Initialize log context.

        Args:
            logger: The logger to use.
            **context: Key-value pairs to add to log messages.
        """
        self.logger = logger
        self.context = context
        self._old_factory: Any = None

    def __enter__(self) -> LogContext:
        """Enter context and configure logging factory."""
        old_factory = logging.getLogRecordFactory()

        def record_factory(
            *args: Any,
            **kwargs: Any,
        ) -> logging.LogRecord:
            record = old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        self._old_factory = old_factory
        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context and restore logging factory."""
        if self._old_factory:
            logging.setLogRecordFactory(self._old_factory)
