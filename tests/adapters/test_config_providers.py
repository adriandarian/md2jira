"""
Tests for configuration providers.
"""

from pathlib import Path
from textwrap import dedent

import pytest

from spectra.adapters.config import (
    EnvironmentConfigProvider,
    FileConfigProvider,
)


class TestFileConfigProvider:
    """Tests for FileConfigProvider."""

    def test_load_yaml_config(self, tmp_path: Path) -> None:
        """Test loading YAML config file."""
        config_file = tmp_path / ".spectra.yaml"
        config_file.write_text(
            dedent(
                """
            jira:
              url: https://example.atlassian.net
              email: user@example.com
              api_token: secret-token
              project: PROJ

            sync:
              verbose: true
              descriptions: true
              subtasks: false

            markdown: /path/to/epic.md
            epic: PROJ-123
        """
            )
        )

        provider = FileConfigProvider(config_path=config_file)
        config = provider.load()

        assert config.tracker.url == "https://example.atlassian.net"
        assert config.tracker.email == "user@example.com"
        assert config.tracker.api_token == "secret-token"
        assert config.tracker.project_key == "PROJ"
        assert config.sync.verbose is True
        assert config.sync.sync_descriptions is True
        assert config.sync.sync_subtasks is False
        assert config.markdown_path == "/path/to/epic.md"
        assert config.epic_key == "PROJ-123"

    def test_load_toml_config(self, tmp_path: Path) -> None:
        """Test loading TOML config file."""
        config_file = tmp_path / ".spectra.toml"
        config_file.write_text(
            dedent(
                """
            markdown = "/path/to/epic.md"
            epic = "PROJ-456"

            [jira]
            url = "https://company.atlassian.net"
            email = "dev@company.com"
            api_token = "api-token-123"

            [sync]
            verbose = false
            execute = true
        """
            )
        )

        provider = FileConfigProvider(config_path=config_file)
        config = provider.load()

        assert config.tracker.url == "https://company.atlassian.net"
        assert config.tracker.email == "dev@company.com"
        assert config.tracker.api_token == "api-token-123"
        assert config.markdown_path == "/path/to/epic.md"
        assert config.epic_key == "PROJ-456"
        assert config.sync.verbose is False
        assert config.sync.dry_run is False  # execute = true

    def test_load_pyproject_toml(self, tmp_path: Path) -> None:
        """Test loading from pyproject.toml [tool.spectra] section."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(
            dedent(
                """
            [project]
            name = "my-project"

            [tool.spectra]
            epic = "PROJ-789"

            [tool.spectra.jira]
            url = "https://test.atlassian.net"
            email = "test@test.com"
            api_token = "test-token"
        """
            )
        )

        provider = FileConfigProvider(config_path=config_file)
        config = provider.load()

        assert config.tracker.url == "https://test.atlassian.net"
        assert config.tracker.email == "test@test.com"
        assert config.epic_key == "PROJ-789"

    def test_config_file_not_found(self, tmp_path: Path) -> None:
        """Test error when specified config file doesn't exist."""
        config_file = tmp_path / "nonexistent.yaml"

        provider = FileConfigProvider(config_path=config_file)
        errors = provider.validate()

        assert any("not found" in err.lower() for err in errors)

    def test_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """Test error on invalid YAML syntax."""
        config_file = tmp_path / ".spectra.yaml"
        config_file.write_text(
            dedent(
                """
            jira:
              url: "unclosed string
              invalid:: yaml
        """
            )
        )

        provider = FileConfigProvider(config_path=config_file)
        errors = provider.validate()

        assert len(errors) > 0
        assert any("yaml" in err.lower() or "syntax" in err.lower() for err in errors)

    def test_invalid_toml_syntax(self, tmp_path: Path) -> None:
        """Test error on invalid TOML syntax."""
        config_file = tmp_path / ".spectra.toml"
        config_file.write_text(
            dedent(
                """
            [jira
            url = invalid
        """
            )
        )

        provider = FileConfigProvider(config_path=config_file)
        errors = provider.validate()

        assert len(errors) > 0

    def test_cli_overrides_take_precedence(self, tmp_path: Path) -> None:
        """Test that CLI overrides take precedence over file config."""
        config_file = tmp_path / ".spectra.yaml"
        config_file.write_text(
            dedent(
                """
            jira:
              url: https://file.atlassian.net
              email: file@example.com
              api_token: file-token

            sync:
              verbose: false
        """
            )
        )

        provider = FileConfigProvider(
            config_path=config_file,
            cli_overrides={"verbose": True, "jira_url": "https://cli.atlassian.net"},
        )

        # CLI override should win
        assert provider.get("sync.verbose") is True

    def test_auto_detect_yaml_in_cwd(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test auto-detection of .spectra.yaml in current directory."""
        monkeypatch.chdir(tmp_path)

        config_file = tmp_path / ".spectra.yaml"
        config_file.write_text(
            dedent(
                """
            jira:
              url: https://auto.atlassian.net
              email: auto@example.com
              api_token: auto-token
        """
            )
        )

        provider = FileConfigProvider()
        config = provider.load()

        assert config.tracker.url == "https://auto.atlassian.net"
        assert provider.config_file_path == config_file

    def test_validate_missing_required_fields(self, tmp_path: Path) -> None:
        """Test validation reports missing required fields."""
        config_file = tmp_path / ".spectra.yaml"
        config_file.write_text(
            dedent(
                """
            jira:
              url: https://example.atlassian.net
            # Missing email and api_token
        """
            )
        )

        provider = FileConfigProvider(config_path=config_file)
        errors = provider.validate()

        assert any("email" in err.lower() for err in errors)
        assert any("api_token" in err.lower() or "token" in err.lower() for err in errors)


class TestEnvironmentConfigProvider:
    """Tests for EnvironmentConfigProvider with file config integration."""

    def test_load_from_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("JIRA_URL", "https://env.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "env@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "env-token")

        provider = EnvironmentConfigProvider()
        config = provider.load()

        assert config.tracker.url == "https://env.atlassian.net"
        assert config.tracker.email == "env@example.com"
        assert config.tracker.api_token == "env-token"

    def test_env_overrides_file_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that environment variables override file config."""
        config_file = tmp_path / ".spectra.yaml"
        config_file.write_text(
            dedent(
                """
            jira:
              url: https://file.atlassian.net
              email: file@example.com
              api_token: file-token
        """
            )
        )

        monkeypatch.setenv("JIRA_URL", "https://env.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "env@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "env-token")

        provider = EnvironmentConfigProvider(config_file=config_file)
        config = provider.load()

        # Environment should override file
        assert config.tracker.url == "https://env.atlassian.net"
        assert config.tracker.email == "env@example.com"
        assert config.tracker.api_token == "env-token"

    def test_cli_overrides_env_and_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that CLI args override both env and file config."""
        config_file = tmp_path / ".spectra.yaml"
        config_file.write_text(
            dedent(
                """
            jira:
              url: https://file.atlassian.net
              email: file@example.com
              api_token: file-token

            sync:
              verbose: false
        """
            )
        )

        monkeypatch.setenv("JIRA_URL", "https://env.atlassian.net")
        monkeypatch.setenv("MD2JIRA_VERBOSE", "false")

        provider = EnvironmentConfigProvider(
            config_file=config_file,
            cli_overrides={"jira_url": "https://cli.atlassian.net", "verbose": True},
        )
        config = provider.load()

        # CLI should override both env and file
        assert config.tracker.url == "https://cli.atlassian.net"
        assert config.sync.verbose is True

    def test_load_from_env_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading from .env file."""
        monkeypatch.chdir(tmp_path)

        env_file = tmp_path / ".env"
        env_file.write_text(
            dedent(
                """
            JIRA_URL=https://dotenv.atlassian.net
            JIRA_EMAIL=dotenv@example.com
            JIRA_API_TOKEN=dotenv-token
        """
            )
        )

        provider = EnvironmentConfigProvider()
        config = provider.load()

        assert config.tracker.url == "https://dotenv.atlassian.net"
        assert config.tracker.email == "dotenv@example.com"

    def test_shows_config_file_in_name(self, tmp_path: Path) -> None:
        """Test that provider name includes config file when loaded."""
        config_file = tmp_path / ".spectra.yaml"
        config_file.write_text(
            dedent(
                """
            jira:
              url: https://example.atlassian.net
              email: test@example.com
              api_token: token
        """
            )
        )

        provider = EnvironmentConfigProvider(config_file=config_file)

        assert ".spectra.yaml" in provider.name

    def test_validation_error_messages_are_actionable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that validation errors include helpful guidance."""
        # Clear any existing env vars
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_EMAIL", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        monkeypatch.chdir(tmp_path)  # Ensure no .env file is found

        provider = EnvironmentConfigProvider()
        errors = provider.validate()

        # Errors should mention multiple config sources
        error_text = " ".join(errors)
        assert "config file" in error_text.lower() or "jira.url" in error_text.lower()
        assert "environment" in error_text.lower() or "JIRA_URL" in error_text


class TestConfigPrecedence:
    """Test configuration precedence: CLI > env > .env > config file."""

    def test_full_precedence_chain(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the full configuration precedence chain."""
        # 1. Config file (lowest priority)
        config_file = tmp_path / ".spectra.yaml"
        config_file.write_text(
            dedent(
                """
            jira:
              url: https://file.atlassian.net
              email: file@example.com
              api_token: file-token
              project: FILE-PROJ

            sync:
              verbose: false
        """
            )
        )

        monkeypatch.chdir(tmp_path)

        # 2. .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            dedent(
                """
            JIRA_URL=https://dotenv.atlassian.net
            JIRA_EMAIL=dotenv@example.com
        """
            )
        )

        # 3. Environment variables
        monkeypatch.setenv("JIRA_URL", "https://env.atlassian.net")

        # 4. CLI overrides (highest priority)
        provider = EnvironmentConfigProvider(
            config_file=config_file,
            cli_overrides={"verbose": True},
        )
        config = provider.load()

        # Verify precedence:
        # - URL: env var wins over .env and file
        assert config.tracker.url == "https://env.atlassian.net"
        # - Email: .env wins over file (no env var or CLI)
        assert config.tracker.email == "dotenv@example.com"
        # - Token: file wins (no higher-priority source)
        assert config.tracker.api_token == "file-token"
        # - Project: file wins (no higher-priority source)
        assert config.tracker.project_key == "FILE-PROJ"
        # - Verbose: CLI wins
        assert config.sync.verbose is True
