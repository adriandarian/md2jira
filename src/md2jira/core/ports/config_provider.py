"""
Configuration Provider Port - Abstract interface for configuration.

Implementations:
- EnvironmentConfigProvider: Load from env vars and .env
- (Future) FileConfigProvider: Load from YAML/TOML config files
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class TrackerConfig:
    """Configuration for an issue tracker."""
    
    url: str
    email: str
    api_token: str
    project_key: Optional[str] = None
    
    # Jira-specific
    story_points_field: str = "customfield_10014"
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.url and self.email and self.api_token)


@dataclass
class SyncConfig:
    """Configuration for sync operations."""
    
    dry_run: bool = True
    confirm_changes: bool = True
    verbose: bool = False
    
    # Phase control
    sync_descriptions: bool = True
    sync_subtasks: bool = True
    sync_comments: bool = True
    sync_statuses: bool = True
    
    # Filters
    story_filter: Optional[str] = None
    
    # Output
    export_path: Optional[str] = None


@dataclass
class AppConfig:
    """Complete application configuration."""
    
    tracker: TrackerConfig
    sync: SyncConfig
    
    # Paths
    markdown_path: Optional[str] = None
    epic_key: Optional[str] = None
    
    def validate(self) -> list[str]:
        """
        Validate configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.tracker.url:
            errors.append("Missing tracker URL (JIRA_URL)")
        if not self.tracker.email:
            errors.append("Missing tracker email (JIRA_EMAIL)")
        if not self.tracker.api_token:
            errors.append("Missing API token (JIRA_API_TOKEN)")
        
        return errors


class ConfigProviderPort(ABC):
    """
    Abstract interface for configuration providers.
    
    Configuration can come from various sources:
    - Environment variables
    - .env files
    - YAML/TOML config files
    - Command line arguments
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the provider name."""
        ...
    
    @abstractmethod
    def load(self) -> AppConfig:
        """
        Load configuration from source.
        
        Returns:
            Complete application configuration
        """
        ...
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        ...
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        ...
    
    @abstractmethod
    def validate(self) -> list[str]:
        """
        Validate loaded configuration.
        
        Returns:
            List of validation errors
        """
        ...

