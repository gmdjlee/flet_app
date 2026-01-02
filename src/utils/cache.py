"""Caching utilities using diskcache for persistent local caching."""

import functools
import hashlib
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from diskcache import Cache, FanoutCache
except ImportError:
    Cache = None
    FanoutCache = None


logger = logging.getLogger(__name__)


def get_cache_dir() -> Path:
    """Get the default cache directory path.

    Returns:
        Path to cache directory.
    """
    import platform

    system = platform.system()
    if system == "Windows":
        cache_dir = Path.home() / "AppData" / "Local" / "dart-db-flet" / "cache"
    elif system == "Darwin":  # macOS
        cache_dir = Path.home() / "Library" / "Caches" / "dart-db-flet"
    else:  # Linux and others
        cache_dir = Path.home() / ".cache" / "dart-db-flet"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


class CacheManager:
    """Manager for disk-based caching using diskcache.

    Provides methods for caching API responses and other data
    to reduce API calls and improve performance.

    Attributes:
        cache: DiskCache instance.
    """

    # Default cache settings
    DEFAULT_EXPIRE = 3600  # 1 hour
    CORP_LIST_EXPIRE = 86400  # 24 hours for corporation list
    CORP_INFO_EXPIRE = 86400  # 24 hours for corporation info
    FINANCIAL_EXPIRE = 604800  # 7 days for financial data

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        size_limit: int = 1024 * 1024 * 500,  # 500 MB default
    ):
        """Initialize cache manager.

        Args:
            cache_dir: Path to cache directory. Uses default if None.
            size_limit: Maximum cache size in bytes.
        """
        if Cache is None:
            logger.warning("diskcache not installed. Caching disabled.")
            self.cache = None
            return

        if cache_dir is None:
            cache_dir = get_cache_dir()

        self.cache_dir = Path(cache_dir)
        self.cache = Cache(
            str(self.cache_dir),
            size_limit=size_limit,
            eviction_policy="least-recently-used",
        )
        logger.info(f"Cache initialized at {self.cache_dir}")

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Create a cache key from prefix and arguments.

        Args:
            prefix: Key prefix (e.g., 'corp_list', 'corp_info').
            *args: Positional arguments to include in key.
            **kwargs: Keyword arguments to include in key.

        Returns:
            Cache key string.
        """
        key_data = {
            "prefix": prefix,
            "args": args,
            "kwargs": sorted(kwargs.items()),
        }
        key_json = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_json.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        if self.cache is None:
            return None

        try:
            return self.cache.get(key)
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            expire: Expiration time in seconds.

        Returns:
            True if successfully cached.
        """
        if self.cache is None:
            return False

        try:
            self.cache.set(key, value, expire=expire or self.DEFAULT_EXPIRE)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key.

        Returns:
            True if successfully deleted.
        """
        if self.cache is None:
            return False

        try:
            return self.cache.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cached data.

        Returns:
            True if successfully cleared.
        """
        if self.cache is None:
            return False

        try:
            self.cache.clear()
            return True
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
            return False

    def get_corporation_list(self, market: str | None = None) -> list[dict] | None:
        """Get cached corporation list.

        Args:
            market: Optional market filter.

        Returns:
            Cached corporation list or None.
        """
        key = self._make_key("corp_list", market=market)
        return self.get(key)

    def set_corporation_list(
        self,
        corps: list[dict],
        market: str | None = None,
    ) -> bool:
        """Cache corporation list.

        Args:
            corps: List of corporation data.
            market: Optional market filter.

        Returns:
            True if successfully cached.
        """
        key = self._make_key("corp_list", market=market)
        return self.set(key, corps, expire=self.CORP_LIST_EXPIRE)

    def get_corporation_info(self, corp_code: str) -> dict | None:
        """Get cached corporation info.

        Args:
            corp_code: Corporation code.

        Returns:
            Cached corporation info or None.
        """
        key = self._make_key("corp_info", corp_code)
        return self.get(key)

    def set_corporation_info(self, corp_code: str, info: dict) -> bool:
        """Cache corporation info.

        Args:
            corp_code: Corporation code.
            info: Corporation info data.

        Returns:
            True if successfully cached.
        """
        key = self._make_key("corp_info", corp_code)
        return self.set(key, info, expire=self.CORP_INFO_EXPIRE)

    def get_financial_statements(
        self,
        corp_code: str,
        bsns_year: str,
        reprt_code: str,
    ) -> list[dict] | None:
        """Get cached financial statements.

        Args:
            corp_code: Corporation code.
            bsns_year: Business year.
            reprt_code: Report code.

        Returns:
            Cached financial statements or None.
        """
        key = self._make_key(
            "financial",
            corp_code=corp_code,
            year=bsns_year,
            reprt=reprt_code,
        )
        return self.get(key)

    def set_financial_statements(
        self,
        corp_code: str,
        bsns_year: str,
        reprt_code: str,
        statements: list[dict],
    ) -> bool:
        """Cache financial statements.

        Args:
            corp_code: Corporation code.
            bsns_year: Business year.
            reprt_code: Report code.
            statements: Financial statement data.

        Returns:
            True if successfully cached.
        """
        key = self._make_key(
            "financial",
            corp_code=corp_code,
            year=bsns_year,
            reprt=reprt_code,
        )
        return self.set(key, statements, expire=self.FINANCIAL_EXPIRE)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary containing cache stats.
        """
        if self.cache is None:
            return {"enabled": False}

        try:
            return {
                "enabled": True,
                "size": len(self.cache),
                "volume": self.cache.volume(),
                "directory": str(self.cache_dir),
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}

    def close(self) -> None:
        """Close cache connection."""
        if self.cache is not None:
            try:
                self.cache.close()
            except Exception as e:
                logger.warning(f"Cache close error: {e}")


# Global cache instance
_cache_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance.

    Returns:
        CacheManager instance.
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(
    prefix: str,
    expire: int | None = None,
) -> Callable:
    """Decorator for caching function results.

    Args:
        prefix: Cache key prefix.
        expire: Expiration time in seconds.

    Returns:
        Decorator function.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache_manager()
            key = cache._make_key(prefix, *args[1:], **kwargs)  # Skip 'self'

            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(key, result, expire=expire)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache_manager()
            key = cache._make_key(prefix, *args[1:], **kwargs)

            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result

            result = func(*args, **kwargs)
            cache.set(key, result, expire=expire)
            return result

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
