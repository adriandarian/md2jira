"""
Jira Adapter - Implementation of IssueTrackerPort for Atlassian Jira.

Includes multiple client options:
- JiraApiClient: Basic synchronous client
- CachedJiraApiClient: Client with response caching
- AsyncJiraApiClient: Async client with parallel request support (requires aiohttp)
- JiraBatchClient: Batch operations using bulk APIs
"""

from .adapter import JiraAdapter
from .client import JiraApiClient
from .cached_client import CachedJiraApiClient
from .batch import JiraBatchClient, BatchResult, BatchOperation

# Async client is optional (requires aiohttp)
try:
    from .async_client import AsyncJiraApiClient
    ASYNC_AVAILABLE = True
except ImportError:
    AsyncJiraApiClient = None  # type: ignore[misc, assignment]
    ASYNC_AVAILABLE = False

__all__ = [
    "JiraAdapter",
    "JiraApiClient",
    "CachedJiraApiClient",
    "JiraBatchClient",
    "BatchResult",
    "BatchOperation",
    "AsyncJiraApiClient",
    "ASYNC_AVAILABLE",
]

