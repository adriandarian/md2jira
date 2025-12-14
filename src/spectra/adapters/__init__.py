"""
Adapters - Concrete implementations of ports.

Subpackages organized by function:
- Trackers: jira/, github/, azure_devops/, linear/, confluence/
- Parsers: parsers/ (markdown, yaml, notion)
- Formatters: formatters/ (adf, markdown)
- Infrastructure: async_base/, cache/, config/
"""

# Trackers
from .jira import JiraAdapter, JiraBatchClient, BatchResult, BatchOperation

# Parsers & Formatters
from .parsers import MarkdownParser
from .formatters import ADFFormatter

# Infrastructure - Config
from .config import EnvironmentConfigProvider

# Infrastructure - Cache
from .cache import (
    CacheBackend,
    CacheEntry,
    CacheStats,
    MemoryCache,
    FileCache,
    CacheManager,
    CacheKeyBuilder,
)

# Infrastructure - Async (optional, requires aiohttp)
try:
    from .async_base import (  # noqa: F401
        AsyncRateLimiter,
        AsyncHttpClient,
        gather_with_limit,
        batch_execute,
        run_parallel,
        ParallelResult,
        ParallelExecutor,
    )
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

__all__ = [
    # Trackers
    "JiraAdapter",
    "JiraBatchClient",
    "BatchResult",
    "BatchOperation",
    # Parsers & Formatters
    "MarkdownParser",
    "ADFFormatter",
    # Infrastructure
    "EnvironmentConfigProvider",
    "CacheBackend",
    "CacheEntry",
    "CacheStats",
    "MemoryCache",
    "FileCache",
    "CacheManager",
    "CacheKeyBuilder",
    "ASYNC_AVAILABLE",
]

