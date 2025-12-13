"""
Adapters - Concrete implementations of ports.

This module contains implementations for:
- Issue Trackers: Jira, GitHub, Linear, Azure DevOps
- Parsers: Markdown, YAML, Notion
- Formatters: ADF (Atlassian Document Format)
- Config: Environment variables
- Async: Parallel API call infrastructure
- Cache: Response caching layer
"""

from .jira import JiraAdapter
from .parsers import MarkdownParser
from .formatters import ADFFormatter
from .config import EnvironmentConfigProvider

# Cache infrastructure
from .cache import (
    CacheBackend,
    CacheEntry,
    CacheStats,
    MemoryCache,
    FileCache,
    CacheManager,
    CacheKeyBuilder,
)

# Async infrastructure (optional, requires aiohttp)
try:
    from .async_base import (
        AsyncRateLimiter,
        AsyncHttpClient,
        gather_with_limit,
        batch_execute,
        run_parallel,
        ParallelResult,
        ParallelExecutor,
    )
    from .async_base.parallel import ParallelExecutor
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

__all__ = [
    "JiraAdapter",
    "MarkdownParser",
    "ADFFormatter",
    "EnvironmentConfigProvider",
    # Cache
    "CacheBackend",
    "CacheEntry",
    "CacheStats",
    "MemoryCache",
    "FileCache",
    "CacheManager",
    "CacheKeyBuilder",
    # Async
    "ASYNC_AVAILABLE",
]

