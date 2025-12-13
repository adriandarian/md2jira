"""
Jira Adapter - Implementation of IssueTrackerPort for Atlassian Jira.

Includes multiple client options:
- JiraApiClient: Basic synchronous client
- CachedJiraApiClient: Client with response caching
- AsyncJiraApiClient: Async client with parallel request support (requires aiohttp)
"""

from .adapter import JiraAdapter
from .client import JiraApiClient
from .cached_client import CachedJiraApiClient

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
    "AsyncJiraApiClient",
    "ASYNC_AVAILABLE",
]

