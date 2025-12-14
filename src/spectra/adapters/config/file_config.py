"""
File Config Provider - Load configuration from YAML or TOML files.

Supports:
- .spectra.yaml / .spectra.yml
- .spectra.toml
- pyproject.toml [tool.spectra] section

Config file search order:
1. Explicit path (--config flag)
2. Current working directory
3. User home directory
"""

import sys
from pathlib import Path
from typing import Any, ClassVar

from spectra.core.ports.config_provider import (
    AppConfig,
    ConfigProviderPort,
    SyncConfig,
    TrackerConfig,
)

# Import ConfigFileError from centralized module and re-export for backward compatibility
from spectra.core.exceptions import ConfigFileError


# TOML support: use stdlib tomllib (3.11+) or tomli fallback (3.10)
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore[import-not-found]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

# YAML support
try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

# ConfigFileError is now imported from core.exceptions and re-exported above
# for backward compatibility. See core/exceptions.py for definition.


class FileConfigProvider(ConfigProviderPort):
    """
    Configuration provider that loads from YAML or TOML config files.

    Supports multiple config file formats and locations, with clear
    error messages for invalid configurations.
    """

    CONFIG_FILES: ClassVar[list[str]] = [
        ".spectra.yaml",
        ".spectra.yml",
        ".spectra.toml",
    ]

    def __init__(
        self,
        config_path: Path | None = None,
        cli_overrides: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the file config provider.

        Args:
            config_path: Explicit path to config file (optional)
            cli_overrides: Command line argument overrides
        """
        self._config_path = config_path
        self._cli_overrides = cli_overrides or {}
        self._values: dict[str, Any] = {}
        self._loaded_from: Path | None = None
        self._load_errors: list[str] = []

        # Load configuration
        self._load_config()
        self._apply_cli_overrides()

    # -------------------------------------------------------------------------
    # ConfigProviderPort Implementation
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        if self._loaded_from:
            return f"File ({self._loaded_from.name})"
        return "File"

    @property
    def config_file_path(self) -> Path | None:
        """Get the path to the loaded config file."""
        return self._loaded_from

    def load(self) -> AppConfig:
        """Load complete configuration."""
        tracker = TrackerConfig(
            url=self._get_nested("jira.url", ""),
            email=self._get_nested("jira.email", ""),
            api_token=self._get_nested("jira.api_token", ""),
            project_key=self._get_nested("jira.project", None),
            story_points_field=self._get_nested(
                "jira.story_points_field", "customfield_10014"
            ),
        )

        sync = SyncConfig(
            dry_run=not self._get_nested("sync.execute", False),
            confirm_changes=not self._get_nested("sync.no_confirm", False),
            verbose=self._get_nested("sync.verbose", False),
            sync_descriptions=self._get_nested("sync.descriptions", True),
            sync_subtasks=self._get_nested("sync.subtasks", True),
            sync_comments=self._get_nested("sync.comments", True),
            sync_statuses=self._get_nested("sync.statuses", True),
            story_filter=self._get_nested("sync.story_filter", None),
            export_path=self._get_nested("sync.export_path", None),
        )

        return AppConfig(
            tracker=tracker,
            sync=sync,
            markdown_path=self._get_nested("markdown", None),
            epic_key=self._get_nested("epic", None),
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        return self._get_nested(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        parts = key.split(".")
        target = self._values

        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]

        target[parts[-1]] = value

    def validate(self) -> list[str]:
        """Validate configuration with clear error messages."""
        errors = list(self._load_errors)

        # Check required Jira settings
        if not self._get_nested("jira.url"):
            errors.append(
                "Missing 'jira.url' - add to config file or set JIRA_URL environment variable"
            )
        if not self._get_nested("jira.email"):
            errors.append(
                "Missing 'jira.email' - add to config file or set JIRA_EMAIL environment variable"
            )
        if not self._get_nested("jira.api_token"):
            errors.append(
                "Missing 'jira.api_token' - add to config file or set JIRA_API_TOKEN environment variable"
            )

        return errors

    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------

    def _get_nested(self, key: str, default: Any = None) -> Any:
        """Get a nested configuration value using dot notation."""
        # CLI overrides take precedence
        flat_key = key.replace(".", "_")
        if flat_key in self._cli_overrides and self._cli_overrides[flat_key] is not None:
            return self._cli_overrides[flat_key]

        # Navigate nested dict
        parts = key.split(".")
        value: Any = self._values

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value if value is not None else default

    def _load_config(self) -> None:
        """Load configuration from file."""
        config_file = self._find_config_file()
        if not config_file:
            return

        self._loaded_from = config_file

        try:
            if config_file.suffix in (".yaml", ".yml"):
                self._load_yaml(config_file)
            elif config_file.name == "pyproject.toml":
                self._load_pyproject_toml(config_file)
            elif config_file.suffix == ".toml":
                self._load_toml(config_file)
        except ConfigFileError as e:
            self._load_errors.append(str(e))
        except Exception as e:
            self._load_errors.append(f"{config_file}: Unexpected error: {e}")

    def _find_config_file(self) -> Path | None:
        """Find config file in standard locations."""
        # Explicit path
        if self._config_path:
            if self._config_path.exists():
                return self._config_path
            self._load_errors.append(f"Config file not found: {self._config_path}")
            return None

        # Search locations
        search_paths = [
            Path.cwd(),
            Path.home(),
        ]

        for base_path in search_paths:
            # Check explicit config files
            for config_name in self.CONFIG_FILES:
                config_path = base_path / config_name
                if config_path.exists():
                    return config_path

            # Check pyproject.toml
            pyproject = base_path / "pyproject.toml"
            if pyproject.exists() and self._has_spectra_section(pyproject):
                return pyproject

        return None

    def _has_spectra_section(self, pyproject_path: Path) -> bool:
        """Check if pyproject.toml has [tool.spectra] section."""
        if tomllib is None:
            return False

        try:
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)
            return "spectra" in data.get("tool", {})
        except Exception:
            return False

    def _load_yaml(self, path: Path) -> None:
        """Load YAML config file."""
        if yaml is None:
            raise ConfigFileError(
                path,
                "PyYAML not installed. Install with: pip install pyyaml",
            )

        try:
            with path.open() as f:
                data = yaml.safe_load(f)
            if data:
                self._values = data
        except yaml.YAMLError as e:
            raise ConfigFileError(path, f"Invalid YAML syntax: {e}") from e

    def _load_toml(self, path: Path) -> None:
        """Load TOML config file."""
        if tomllib is None:
            raise ConfigFileError(
                path,
                "TOML support not available. Install with: pip install tomli",
            )

        try:
            with path.open("rb") as f:
                self._values = tomllib.load(f)
        except Exception as e:
            raise ConfigFileError(path, f"Invalid TOML syntax: {e}") from e

    def _load_pyproject_toml(self, path: Path) -> None:
        """Load config from pyproject.toml [tool.spectra] section."""
        if tomllib is None:
            raise ConfigFileError(
                path,
                "TOML support not available. Install with: pip install tomli",
            )

        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
            spectra_config = data.get("tool", {}).get("spectra", {})
            if spectra_config:
                self._values = spectra_config
        except Exception as e:
            raise ConfigFileError(path, f"Invalid TOML syntax: {e}") from e

    def _apply_cli_overrides(self) -> None:
        """Apply CLI argument overrides."""
        # Map CLI args to nested config keys
        cli_mapping = {
            "markdown": "markdown",
            "epic": "epic",
            "project": "jira.project",
            "jira_url": "jira.url",
            "story": "sync.story_filter",
            "execute": "sync.execute",
            "no_confirm": "sync.no_confirm",
            "verbose": "sync.verbose",
        }

        for cli_key, config_key in cli_mapping.items():
            if cli_key in self._cli_overrides and self._cli_overrides[cli_key] is not None:
                self.set(config_key, self._cli_overrides[cli_key])

