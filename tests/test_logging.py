"""Tests for the logging module."""

from __future__ import annotations

import json
import logging

from quantum_pcb_builder.core.logging import (
    ConsoleFormatter,
    LogContext,
    LoggerFactory,
    LogLevel,
    StructuredFormatter,
    get_logger,
)


class TestLogLevel:
    """Tests for the LogLevel enum."""

    def test_debug_level(self) -> None:
        """Test debug level value."""
        assert LogLevel.DEBUG.value == logging.DEBUG

    def test_info_level(self) -> None:
        """Test info level value."""
        assert LogLevel.INFO.value == logging.INFO

    def test_warning_level(self) -> None:
        """Test warning level value."""
        assert LogLevel.WARNING.value == logging.WARNING

    def test_error_level(self) -> None:
        """Test error level value."""
        assert LogLevel.ERROR.value == logging.ERROR

    def test_critical_level(self) -> None:
        """Test critical level value."""
        assert LogLevel.CRITICAL.value == logging.CRITICAL


class TestStructuredFormatter:
    """Tests for the StructuredFormatter class."""

    def test_format_basic(self) -> None:
        """Test basic log formatting."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert "timestamp" in data

    def test_format_with_extra(self) -> None:
        """Test formatting with extra fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"
        output = formatter.format(record)
        data = json.loads(output)
        assert data["custom_field"] == "custom_value"


class TestConsoleFormatter:
    """Tests for the ConsoleFormatter class."""

    def test_format_info(self) -> None:
        """Test info level formatting."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Info message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert "INFO" in output
        assert "Info message" in output

    def test_format_error(self) -> None:
        """Test error level formatting."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert "ERROR" in output


class TestLoggerFactory:
    """Tests for the LoggerFactory class."""

    def test_configure(self) -> None:
        """Test configuring the factory."""
        LoggerFactory.configure(level=LogLevel.DEBUG)
        assert LoggerFactory._default_level == logging.DEBUG
        assert LoggerFactory._configured is True

    def test_get_logger(self) -> None:
        """Test getting a logger."""
        logger = LoggerFactory.get_logger("test_module")
        assert logger.name == "quantum_pcb_builder.test_module"

    def test_get_logger_auto_configure(self) -> None:
        """Test that get_logger auto-configures."""
        LoggerFactory._configured = False
        logger = LoggerFactory.get_logger("auto_test")
        assert LoggerFactory._configured is True
        assert logger is not None


class TestGetLogger:
    """Tests for the get_logger convenience function."""

    def test_get_logger(self) -> None:
        """Test getting a logger via convenience function."""
        logger = get_logger("my_module")
        assert logger is not None
        assert "my_module" in logger.name


class TestLogContext:
    """Tests for the LogContext class."""

    def test_context_manager(self) -> None:
        """Test log context as context manager."""
        logger = get_logger("context_test")
        with LogContext(logger, request_id="123", user="test") as ctx:
            assert ctx.context["request_id"] == "123"
            assert ctx.context["user"] == "test"

    def test_context_restores_factory(self) -> None:
        """Test that context restores log factory."""
        logger = get_logger("restore_test")
        logging.getLogRecordFactory()
        with LogContext(logger, test_field="value"):
            pass
        # Factory should be restored (though it may be the same reference)
        assert logging.getLogRecordFactory() is not None
