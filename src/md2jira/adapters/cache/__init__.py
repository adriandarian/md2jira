"""
Cache Module - Caching layer for API responses.

Provides caching to reduce API calls and improve performance:
- CacheBackend: Abstract interface for cache storage
- MemoryCache: In-memory LRU cache with TTL support
- FileCache: File-based persistent cache
- CacheManager: High-level cache management

Example:
    >>> from md2jira.adapters.cache import MemoryCache, CachedClient
    >>> 
    >>> cache = MemoryCache(max_size=1000, default_ttl=300)
    >>> client = CachedClient(jira_client, cache)
    >>> 
    >>> # First call hits API
    >>> issue = client.get_issue("PROJ-123")
    >>> 
    >>> # Second call uses cache
    >>> issue = client.get_issue("PROJ-123")
"""

from .backend import CacheBackend, CacheEntry, CacheStats
from .memory import MemoryCache
from .file_cache import FileCache
from .manager import CacheManager
from .keys import CacheKeyBuilder

__all__ = [
    "CacheBackend",
    "CacheEntry", 
    "CacheStats",
    "MemoryCache",
    "FileCache",
    "CacheManager",
    "CacheKeyBuilder",
]

