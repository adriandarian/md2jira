"""
Plugin Base Classes - Abstract base for all plugins.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional, Type


class PluginType(Enum):
    """Types of plugins supported."""
    
    PARSER = auto()      # Input format parsers
    TRACKER = auto()     # Issue trackers
    FORMATTER = auto()   # Output formatters
    HOOK = auto()        # Processing hooks
    COMMAND = auto()     # Custom commands


@dataclass
class PluginMetadata:
    """Metadata about a plugin."""
    
    name: str
    version: str
    description: str
    author: Optional[str] = None
    plugin_type: PluginType = PluginType.HOOK
    
    # Dependencies on other plugins
    requires: list[str] = None
    
    # Configuration schema (for validation)
    config_schema: Optional[dict] = None
    
    def __post_init__(self):
        if self.requires is None:
            self.requires = []


class Plugin(ABC):
    """
    Abstract base class for all plugins.
    
    Plugins must implement:
    - metadata property
    - initialize() method
    - Optional: shutdown() method
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize plugin with optional config.
        
        Args:
            config: Plugin-specific configuration
        """
        self.config = config or {}
        self._initialized = False
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        ...
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the plugin.
        
        Called when plugin is loaded. Should set up any resources needed.
        """
        ...
    
    def shutdown(self) -> None:
        """
        Shutdown the plugin.
        
        Called when plugin is unloaded. Should clean up resources.
        """
        pass
    
    def validate_config(self) -> list[str]:
        """
        Validate plugin configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        schema = self.metadata.config_schema
        if not schema:
            return errors
        
        # Check required fields
        for field, field_schema in schema.get("properties", {}).items():
            if field_schema.get("required") and field not in self.config:
                errors.append(f"Missing required config: {field}")
        
        return errors
    
    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized


class ParserPlugin(Plugin):
    """Base class for parser plugins."""
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.PARSER
    
    @abstractmethod
    def get_parser(self) -> Any:
        """Get the parser instance (must implement DocumentParserPort)."""
        ...


class TrackerPlugin(Plugin):
    """Base class for tracker plugins."""
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TRACKER
    
    @abstractmethod
    def get_tracker(self) -> Any:
        """Get the tracker instance (must implement IssueTrackerPort)."""
        ...


class FormatterPlugin(Plugin):
    """Base class for formatter plugins."""
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.FORMATTER
    
    @abstractmethod
    def get_formatter(self) -> Any:
        """Get the formatter instance (must implement DocumentFormatterPort)."""
        ...

