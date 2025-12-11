"""
Adapters - Concrete implementations of ports.

This module contains implementations for:
- Issue Trackers: Jira, (future: GitHub, Linear)
- Parsers: Markdown, (future: YAML)
- Formatters: ADF (Atlassian Document Format)
- Config: Environment variables
"""

from .jira import JiraAdapter
from .parsers import MarkdownParser
from .formatters import ADFFormatter
from .config import EnvironmentConfigProvider

__all__ = [
    "JiraAdapter",
    "MarkdownParser",
    "ADFFormatter",
    "EnvironmentConfigProvider",
]

