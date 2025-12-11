"""
Environment Config Provider - Load configuration from environment variables.

Supports:
- Environment variables (JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN)
- .env files
- Command line argument overrides
"""

import os
from pathlib import Path
from typing import Any, Optional, Union

from ...core.ports.config_provider import (
    ConfigProviderPort,
    AppConfig,
    TrackerConfig,
    SyncConfig,
)


class EnvironmentConfigProvider(ConfigProviderPort):
    """
    Configuration provider that loads from environment variables and .env files.
    """
    
    ENV_PREFIX = "JIRA_"
    
    def __init__(
        self,
        env_file: Optional[Path] = None,
        cli_overrides: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize the config provider.
        
        Args:
            env_file: Path to .env file (auto-detected if not specified)
            cli_overrides: Command line argument overrides
        """
        self._values: dict[str, Any] = {}
        self._env_file = env_file
        self._cli_overrides = cli_overrides or {}
        
        # Load configuration
        self._load_env_file()
        self._load_environment()
        self._apply_cli_overrides()
    
    # -------------------------------------------------------------------------
    # ConfigProviderPort Implementation
    # -------------------------------------------------------------------------
    
    @property
    def name(self) -> str:
        return "Environment"
    
    def load(self) -> AppConfig:
        """Load complete configuration."""
        tracker = TrackerConfig(
            url=self.get("jira_url", ""),
            email=self.get("jira_email", ""),
            api_token=self.get("jira_api_token", ""),
            project_key=self.get("project_key"),
            story_points_field=self.get("story_points_field", "customfield_10014"),
        )
        
        sync = SyncConfig(
            dry_run=not self.get("execute", False),
            confirm_changes=not self.get("no_confirm", False),
            verbose=self.get("verbose", False),
            sync_descriptions=self.get("sync_descriptions", True),
            sync_subtasks=self.get("sync_subtasks", True),
            sync_comments=self.get("sync_comments", True),
            sync_statuses=self.get("sync_statuses", True),
            story_filter=self.get("story_filter"),
            export_path=self.get("export_path"),
        )
        
        return AppConfig(
            tracker=tracker,
            sync=sync,
            markdown_path=self.get("markdown_path"),
            epic_key=self.get("epic_key"),
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        # Normalize key
        key = key.lower().replace("-", "_")
        
        # Check CLI overrides first
        if key in self._cli_overrides:
            return self._cli_overrides[key]
        
        # Check loaded values
        return self._values.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        key = key.lower().replace("-", "_")
        self._values[key] = value
    
    def validate(self) -> list[str]:
        """Validate configuration."""
        errors = []
        
        if not self.get("jira_url"):
            errors.append("Missing JIRA_URL - set in environment or .env file")
        if not self.get("jira_email"):
            errors.append("Missing JIRA_EMAIL - set in environment or .env file")
        if not self.get("jira_api_token"):
            errors.append("Missing JIRA_API_TOKEN - set in environment or .env file")
        
        return errors
    
    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------
    
    def _load_env_file(self) -> None:
        """Load values from .env file."""
        env_file = self._find_env_file()
        if not env_file:
            return
        
        for line in env_file.read_text().splitlines():
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Parse key=value
            if "=" not in line:
                continue
            
            key, value = line.split("=", 1)
            key = key.strip().lower()
            value = value.strip().strip('"').strip("'")
            
            self._values[key] = value
    
    def _find_env_file(self) -> Optional[Path]:
        """Find .env file."""
        if self._env_file and self._env_file.exists():
            return self._env_file
        
        # Check current directory
        cwd_env = Path.cwd() / ".env"
        if cwd_env.exists():
            return cwd_env
        
        # Check package directory
        pkg_env = Path(__file__).parent.parent.parent.parent / ".env"
        if pkg_env.exists():
            return pkg_env
        
        return None
    
    def _load_environment(self) -> None:
        """Load values from environment variables."""
        env_mapping = {
            "JIRA_URL": "jira_url",
            "JIRA_EMAIL": "jira_email",
            "JIRA_API_TOKEN": "jira_api_token",
            "JIRA_PROJECT": "project_key",
            "MD2JIRA_VERBOSE": "verbose",
        }
        
        for env_key, config_key in env_mapping.items():
            raw_value = os.environ.get(env_key)
            if raw_value is not None:
                # Convert boolean-ish values
                final_value: Any
                if raw_value.lower() in ("true", "1", "yes"):
                    final_value = True
                elif raw_value.lower() in ("false", "0", "no"):
                    final_value = False
                else:
                    final_value = raw_value
                
                self._values[config_key] = final_value
    
    def _apply_cli_overrides(self) -> None:
        """Apply CLI argument overrides."""
        # Map CLI args to config keys
        cli_mapping = {
            "markdown": "markdown_path",
            "epic": "epic_key",
            "project": "project_key",
            "jira_url": "jira_url",
            "story": "story_filter",
            "execute": "execute",
            "no_confirm": "no_confirm",
            "verbose": "verbose",
        }
        
        for cli_key, config_key in cli_mapping.items():
            if cli_key in self._cli_overrides and self._cli_overrides[cli_key] is not None:
                self._values[config_key] = self._cli_overrides[cli_key]

