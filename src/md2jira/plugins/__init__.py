"""
Plugin System - Extensibility for md2jira.

Plugins can extend:
- Parsers: Support new input formats (YAML, JSON, etc.)
- Trackers: Support new issue trackers (GitHub, Linear, etc.)
- Formatters: Support new output formats
- Hooks: Add pre/post processing
"""

from .registry import PluginRegistry
from .base import Plugin, PluginType, PluginMetadata
from .hooks import Hook, HookPoint, HookManager, HookContext

__all__ = [
    "PluginRegistry",
    "Plugin",
    "PluginType",
    "PluginMetadata",
    "Hook",
    "HookPoint",
    "HookManager",
    "HookContext",
]

