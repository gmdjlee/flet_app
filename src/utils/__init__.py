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
from src.utils.formatters import (
    format_amount,
    format_amount_short,
    format_corp_cls,
    format_date,
    format_growth,
    format_percentage,
    format_ratio,
    format_report_code,
    format_statement_type,
    get_growth_color,
    get_ratio_status,
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
    # Formatters
    "format_amount",
    "format_amount_short",
    "format_percentage",
    "format_growth",
    "format_ratio",
    "format_date",
    "format_corp_cls",
    "format_report_code",
    "format_statement_type",
    "get_growth_color",
    "get_ratio_status",
]
