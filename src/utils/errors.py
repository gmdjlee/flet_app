"""Custom exception classes and error handling utilities."""

import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Error code enumeration for categorizing errors."""

    # General errors (1000-1999)
    UNKNOWN = 1000
    VALIDATION = 1001
    NOT_FOUND = 1002
    ALREADY_EXISTS = 1003

    # API errors (2000-2999)
    API_ERROR = 2000
    API_KEY_MISSING = 2001
    API_KEY_INVALID = 2002
    API_RATE_LIMIT = 2003
    API_TIMEOUT = 2004
    API_CONNECTION = 2005

    # Database errors (3000-3999)
    DB_ERROR = 3000
    DB_CONNECTION = 3001
    DB_INTEGRITY = 3002
    DB_NOT_FOUND = 3003

    # Sync errors (4000-4999)
    SYNC_ERROR = 4000
    SYNC_CANCELLED = 4001
    SYNC_IN_PROGRESS = 4002


class DartDbError(Exception):
    """Base exception for DART-DB application errors.

    Attributes:
        message: Human-readable error message.
        code: ErrorCode enumeration value.
        details: Additional error details.
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN,
        details: dict[str, Any] | None = None,
    ):
        """Initialize exception.

        Args:
            message: Error message.
            code: Error code.
            details: Additional details dictionary.
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation."""
        return f"[{self.code.name}] {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary.

        Returns:
            Dictionary containing error information.
        """
        return {
            "error": True,
            "code": self.code.value,
            "code_name": self.code.name,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(DartDbError):
    """Exception for validation errors."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize validation error.

        Args:
            message: Error message.
            field: Field name that failed validation.
            details: Additional details.
        """
        if field:
            details = details or {}
            details["field"] = field

        super().__init__(message, ErrorCode.VALIDATION, details)


class NotFoundError(DartDbError):
    """Exception for resource not found errors."""

    def __init__(
        self,
        resource: str,
        identifier: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize not found error.

        Args:
            resource: Resource type (e.g., 'Corporation', 'Filing').
            identifier: Resource identifier.
            details: Additional details.
        """
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
            details = details or {}
            details["identifier"] = identifier

        super().__init__(message, ErrorCode.NOT_FOUND, details)


class ApiError(DartDbError):
    """Exception for API-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.API_ERROR,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize API error.

        Args:
            message: Error message.
            code: Specific API error code.
            status_code: HTTP status code if applicable.
            details: Additional details.
        """
        details = details or {}
        if status_code:
            details["status_code"] = status_code

        super().__init__(message, code, details)


class DatabaseError(DartDbError):
    """Exception for database-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.DB_ERROR,
        details: dict[str, Any] | None = None,
    ):
        """Initialize database error.

        Args:
            message: Error message.
            code: Specific database error code.
            details: Additional details.
        """
        super().__init__(message, code, details)


class SyncError(DartDbError):
    """Exception for synchronization errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.SYNC_ERROR,
        details: dict[str, Any] | None = None,
    ):
        """Initialize sync error.

        Args:
            message: Error message.
            code: Specific sync error code.
            details: Additional details.
        """
        super().__init__(message, code, details)


def handle_exception(
    exc: Exception,
    context: str = "",
    log_level: int = logging.ERROR,
) -> DartDbError:
    """Convert any exception to DartDbError.

    Args:
        exc: Original exception.
        context: Context information for logging.
        log_level: Logging level.

    Returns:
        DartDbError instance.
    """
    if isinstance(exc, DartDbError):
        logger.log(log_level, f"{context}: {exc}")
        return exc

    # Convert known exceptions
    message = str(exc)

    if "timeout" in message.lower():
        error = ApiError(message, ErrorCode.API_TIMEOUT)
    elif "connection" in message.lower():
        error = ApiError(message, ErrorCode.API_CONNECTION)
    elif "rate limit" in message.lower():
        error = ApiError(message, ErrorCode.API_RATE_LIMIT)
    else:
        error = DartDbError(message, ErrorCode.UNKNOWN, {"original": type(exc).__name__})

    logger.log(log_level, f"{context}: {error}")
    return error


class ErrorHandler:
    """Context manager and utility class for error handling."""

    def __init__(self, context: str = "", suppress: bool = False):
        """Initialize error handler.

        Args:
            context: Context description for logging.
            suppress: If True, suppress exceptions after logging.
        """
        self.context = context
        self.suppress = suppress
        self.error: DartDbError | None = None

    def __enter__(self) -> "ErrorHandler":
        """Enter context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context and handle any exception.

        Returns:
            True to suppress exception if configured.
        """
        if exc_val is not None:
            self.error = handle_exception(exc_val, self.context)

            if self.suppress:
                return True

        return False

    @property
    def has_error(self) -> bool:
        """Check if an error occurred."""
        return self.error is not None
