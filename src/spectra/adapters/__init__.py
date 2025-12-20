"""
Adapters - Concrete implementations of ports.

Subpackages organized by function:
- Trackers: jira/, github/, azure_devops/, linear/, confluence/
- Parsers: parsers/ (markdown, yaml, notion)
- Formatters: formatters/ (adf, markdown)
- Infrastructure: async_base/, cache/, config/
"""

# Trackers
# Infrastructure - Cache
from .asana import AsanaAdapter
from .cache import (
    CacheBackend,
    CacheEntry,
    CacheKeyBuilder,
    CacheManager,
    CacheStats,
    FileCache,
    MemoryCache,
)

# Infrastructure - Config
from .config import EnvironmentConfigProvider
from .formatters import ADFFormatter
from .jira import BatchOperation, BatchResult, JiraAdapter, JiraBatchClient

# Parsers & Formatters
from .parsers import MarkdownParser


# Infrastructure - Async (optional, requires aiohttp)
try:
    from .async_base import (
        AsyncHttpClient,
        AsyncRateLimiter,
        ParallelExecutor,
        ParallelResult,
        batch_execute,
        gather_with_limit,
        run_parallel,
    )

    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

__all__ = [
    "ASYNC_AVAILABLE",
    "ADFFormatter",
    "AsanaAdapter",
    "BatchOperation",
    "BatchResult",
    "CacheBackend",
    "CacheEntry",
    "CacheKeyBuilder",
    "CacheManager",
    "CacheStats",
    # Infrastructure
    "EnvironmentConfigProvider",
    "FileCache",
    # Trackers
    "JiraAdapter",
    "JiraBatchClient",
    # Parsers & Formatters
    "MarkdownParser",
    "MemoryCache",
]
