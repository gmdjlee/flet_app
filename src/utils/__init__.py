"""Utility functions package."""

from src.utils.cache import (
    CacheManager,
    cached,
    get_cache_dir,
    get_cache_manager,
)
from src.utils.errors import (
    ApiError,
    DartDbError,
    DatabaseError,
    ErrorCode,
    ErrorHandler,
    NotFoundError,
    SyncError,
    ValidationError,
    handle_exception,
)

__all__ = [
    # Cache
    "CacheManager",
    "get_cache_manager",
    "get_cache_dir",
    "cached",
    # Errors
    "DartDbError",
    "ValidationError",
    "NotFoundError",
    "ApiError",
    "DatabaseError",
    "SyncError",
    "ErrorCode",
    "ErrorHandler",
    "handle_exception",
]
