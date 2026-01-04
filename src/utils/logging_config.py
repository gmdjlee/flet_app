"""Centralized logging configuration for DART-DB application."""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

# Project root directory (src/utils/logging_config.py -> project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Default log directory in project root
LOG_DIR = PROJECT_ROOT / "log"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log file settings
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB
BACKUP_COUNT = 5  # Keep 5 backup files


class LogConfig:
    """Configuration class for application logging."""

    _initialized: bool = False
    _log_dir: Path = LOG_DIR
    _log_level: int = logging.INFO

    @classmethod
    def setup(
        cls,
        log_dir: Path | None = None,
        log_level: int = logging.INFO,
        console_output: bool = True,
        file_output: bool = True,
    ) -> None:
        """Set up logging configuration for the application.

        Args:
            log_dir: Directory for log files. Defaults to project_root/log
            log_level: Logging level (default: INFO)
            console_output: Enable console logging (default: True)
            file_output: Enable file logging (default: True)
        """
        if cls._initialized:
            return

        cls._log_dir = log_dir or LOG_DIR
        cls._log_level = log_level

        # Ensure log directory exists
        cls._log_dir.mkdir(parents=True, exist_ok=True)

        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # File handler with rotation
        if file_output:
            log_file = cls._log_dir / "dart-db.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=MAX_LOG_SIZE,
                backupCount=BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            # Error log file (only errors and above)
            error_log_file = cls._log_dir / "dart-db-error.log"
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=MAX_LOG_SIZE,
                backupCount=BACKUP_COUNT,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)

        cls._initialized = True

        # Log initialization
        logger = logging.getLogger(__name__)
        logger.info("Logging initialized")
        logger.info(f"Log directory: {cls._log_dir}")
        logger.info(f"Log level: {logging.getLevelName(log_level)}")

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance with the given name.

        Args:
            name: Logger name (usually __name__)

        Returns:
            Logger instance
        """
        if not cls._initialized:
            cls.setup()
        return logging.getLogger(name)

    @classmethod
    def set_level(cls, level: int) -> None:
        """Set logging level for all loggers.

        Args:
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        cls._log_level = level
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        for handler in root_logger.handlers:
            if not isinstance(handler, RotatingFileHandler) or "error" not in str(handler.baseFilename).lower():
                handler.setLevel(level)

    @classmethod
    def get_log_dir(cls) -> Path:
        """Get the log directory path.

        Returns:
            Path to log directory
        """
        return cls._log_dir

    @classmethod
    def get_recent_logs(cls, lines: int = 100) -> list[str]:
        """Get recent log entries from the main log file.

        Args:
            lines: Number of recent lines to return

        Returns:
            List of log lines
        """
        log_file = cls._log_dir / "dart-db.log"
        if not log_file.exists():
            return []

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                return all_lines[-lines:]
        except (OSError, IOError):
            return []

    @classmethod
    def cleanup_old_logs(cls, days: int = 30) -> int:
        """Clean up log files older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of files deleted
        """
        if not cls._log_dir.exists():
            return 0

        deleted = 0
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for log_file in cls._log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff:
                try:
                    log_file.unlink()
                    deleted += 1
                except OSError:
                    pass

        return deleted


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return LogConfig.get_logger(name)


def setup_logging(
    log_level: int = logging.INFO,
    console_output: bool = True,
    file_output: bool = True,
) -> None:
    """Convenience function to set up logging.

    Args:
        log_level: Logging level
        console_output: Enable console logging
        file_output: Enable file logging
    """
    LogConfig.setup(
        log_level=log_level,
        console_output=console_output,
        file_output=file_output,
    )


class LoggingMixin:
    """Mixin class that provides logging capability to any class.

    Example:
        class MyService(LoggingMixin):
            def do_something(self):
                self.logger.info("Doing something")
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__module__ + "." + self.__class__.__name__)
        return self._logger


def log_function_call(logger: logging.Logger | None = None):
    """Decorator to log function calls.

    Args:
        logger: Logger instance. If None, creates one from function module.

    Returns:
        Decorator function
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)

        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} failed: {e}")
                raise

        async def async_wrapper(*args, **kwargs):
            logger.debug(f"Calling async {func.__name__}")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} failed: {e}")
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator
