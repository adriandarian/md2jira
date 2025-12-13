"""
Confluence Adapter - Sync epics and stories to Confluence pages.
"""

from .client import ConfluenceClient
from .adapter import ConfluenceAdapter
from .plugin import ConfluencePlugin, create_plugin

__all__ = [
    "ConfluenceClient",
    "ConfluenceAdapter",
    "ConfluencePlugin",
    "create_plugin",
]

