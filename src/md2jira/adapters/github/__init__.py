"""
GitHub Issues Adapter - Integration with GitHub Issues.

This module provides the GitHub Issues implementation of the IssueTrackerPort,
enabling syncing markdown documents to GitHub Issues.
"""

from .client import GitHubApiClient
from .adapter import GitHubAdapter
from .plugin import GitHubTrackerPlugin

__all__ = [
    "GitHubApiClient",
    "GitHubAdapter",
    "GitHubTrackerPlugin",
]

