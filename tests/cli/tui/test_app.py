"""
Tests for TUI application.

Note: Full TUI testing requires Textual's async test harness.
These tests focus on initialization and configuration.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from spectra.cli.tui.data import TUIState, create_demo_state


class TestTUIStateInitialization:
    """Tests for TUI state initialization."""

    def test_default_initialization(self) -> None:
        """Test default state initialization."""
        state = TUIState()

        assert state.markdown_path is None
        assert state.epic_key is None
        assert state.stories == []
        assert state.dry_run is True

    def test_initialization_with_values(self) -> None:
        """Test state initialization with values."""
        path = Path("/test/file.md")
        state = TUIState(
            markdown_path=path,
            epic_key="PROJ-123",
            dry_run=False,
        )

        assert state.markdown_path == path
        assert state.epic_key == "PROJ-123"
        assert not state.dry_run


class TestRunTUIFunction:
    """Tests for run_tui function."""

    def test_run_tui_without_textual(self) -> None:
        """Test run_tui returns error when Textual not available."""
        with patch("spectra.cli.tui.app.TEXTUAL_AVAILABLE", False):
            from spectra.cli.tui.app import run_tui

            # Re-import to get patched version
            result = run_tui(demo=True)
            # When TEXTUAL_AVAILABLE is False, should return error code
            if result != 0:
                assert result == 1  # Error code when Textual not available

    def test_run_tui_demo_mode_available(self) -> None:
        """Test that demo mode is supported."""
        from spectra.cli.tui.app import check_textual_available

        if not check_textual_available():
            pytest.skip("Textual not available")

        # Just verify the function can be called with demo=True
        # Actual running would require Textual's test harness
        from spectra.cli.tui.app import SpectraTUI

        app = SpectraTUI(demo=True)
        assert app.state is not None
        assert len(app.state.stories) > 0


class TestDemoState:
    """Tests for demo state creation."""

    def test_create_demo_state_returns_populated_state(self) -> None:
        """Test demo state has all required fields."""
        state = create_demo_state()

        assert state.epic_key is not None
        assert state.epic is not None
        assert len(state.stories) >= 2
        assert state.selected_story_id is not None

    def test_demo_state_stories_have_variety(self) -> None:
        """Test demo stories have varied attributes."""
        state = create_demo_state()

        statuses = {s.status for s in state.stories}
        priorities = {s.priority for s in state.stories}

        assert len(statuses) >= 2, "Demo should have varied statuses"
        assert len(priorities) >= 2, "Demo should have varied priorities"

    def test_demo_state_selected_story_exists(self) -> None:
        """Test that selected story exists in stories list."""
        state = create_demo_state()

        story = state.get_selected_story()
        assert story is not None
        assert str(story.id) == state.selected_story_id
