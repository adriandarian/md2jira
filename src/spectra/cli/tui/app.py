"""
TUI App - Main Textual application for Spectra.

Provides the interactive TUI dashboard with:
- Story browser with tree navigation
- Real-time sync progress
- Conflict resolution
- Statistics and logs
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any


try:
    from textual import on
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical
    from textual.screen import Screen
    from textual.widgets import (
        Footer,
        Header,
        Rule,
        Static,
        TabbedContent,
        TabPane,
    )

    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    if TYPE_CHECKING:
        from textual.app import App, ComposeResult

from spectra.cli.tui.data import (
    SyncProgress,
    TUIState,
    create_demo_state,
    load_stories_from_file,
)
from spectra.cli.tui.widgets import (
    ConflictPanel,
    LogPanel,
    StatsPanel,
    StoryBrowser,
    StoryDetail,
    SyncProgressPanel,
)


# =============================================================================
# CSS Styles
# =============================================================================

SPECTRA_CSS = """
/* Base theme - Deep space aesthetic */
Screen {
    background: $surface;
}

/* Header styling */
Header {
    background: $primary-darken-3;
    color: $text;
}

/* Sidebar */
#sidebar {
    width: 35;
    background: $surface-darken-1;
    border-right: solid $primary-darken-2;
    padding: 1;
}

/* Main content area */
#main-content {
    background: $surface;
    padding: 1;
}

/* Panel titles */
.panel-title {
    text-style: bold;
    color: $primary-lighten-2;
    padding: 0 1;
}

/* Story tree */
#story-tree {
    height: 100%;
    scrollbar-gutter: stable;
}

Tree {
    background: transparent;
}

Tree > .tree--cursor {
    background: $primary;
    color: $text;
}

Tree > .tree--highlight {
    background: $primary-darken-1;
}

/* Stats panel */
#stats-container {
    height: auto;
    max-height: 20;
    padding: 1;
    background: $surface-darken-1;
    border: solid $primary-darken-2;
    margin-bottom: 1;
}

/* Sync progress panel */
#sync-panel {
    height: auto;
    padding: 1;
    background: $surface-darken-1;
    border: solid $primary-darken-2;
    margin-bottom: 1;
}

ProgressBar {
    padding: 0 1;
}

ProgressBar > .bar--complete {
    color: $success;
}

ProgressBar > .bar--bar {
    color: $primary;
}

/* Detail panel */
#detail-container {
    padding: 1;
    background: $surface-darken-1;
    border: solid $primary-darken-2;
}

#detail-content {
    padding: 1;
}

/* Conflict panel */
#conflict-container {
    padding: 1;
    background: $warning-darken-3;
    border: solid $warning;
}

#conflict-diff {
    height: auto;
    min-height: 10;
}

.diff-side {
    width: 1fr;
    padding: 1;
    margin: 0 1;
    background: $surface;
    border: solid $border;
}

.diff-label {
    text-align: center;
    padding-bottom: 1;
}

.diff-content {
    padding: 1;
}

#conflict-actions {
    height: auto;
    padding-top: 1;
    align: center middle;
}

#conflict-actions Button {
    margin: 0 1;
}

/* Log panel */
#log-container {
    height: auto;
    max-height: 15;
    padding: 1;
    background: $surface-darken-1;
    border: solid $primary-darken-2;
}

#log-scroll {
    height: auto;
    max-height: 10;
}

/* Tabs */
TabbedContent {
    background: transparent;
}

TabPane {
    padding: 1;
}

/* Actions bar */
#actions-bar {
    height: auto;
    dock: bottom;
    padding: 1;
    background: $surface-darken-2;
    border-top: solid $primary-darken-2;
}

#actions-bar Button {
    margin: 0 1;
}

/* Footer */
Footer {
    background: $primary-darken-3;
}

/* Search input */
#search-input {
    dock: top;
    margin: 1;
}

/* Status bar */
#status-bar {
    height: 1;
    dock: bottom;
    background: $surface-darken-2;
    padding: 0 1;
}

/* Buttons */
Button {
    min-width: 12;
}

Button.-primary {
    background: $primary;
}

Button.-success {
    background: $success;
}

Button.-warning {
    background: $warning;
}

Button.-error {
    background: $error;
}

/* Rule styling */
Rule {
    margin: 1 0;
    color: $primary-darken-2;
}
"""


# =============================================================================
# Main Dashboard Screen
# =============================================================================


class DashboardScreen(Screen):
    """Main dashboard screen with story browser and details."""

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("s", "sync", "Sync", show=True),
        Binding("d", "toggle_dry_run", "Dry Run", show=True),
        Binding("f", "filter", "Filter", show=False),
        Binding("/", "search", "Search", show=False),
        Binding("?", "help", "Help", show=True),
        Binding("c", "conflicts", "Conflicts", show=False),
        Binding("escape", "clear_search", "Clear", show=False),
    ]

    def __init__(self, state: TUIState, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.state = state
        self._log_panel: LogPanel | None = None

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        yield Header(show_clock=True)

        with Horizontal(id="main-layout"):
            # Left sidebar - Story browser
            with Vertical(id="sidebar"):
                yield StatsPanel(self.state.stories, id="stats-panel")
                yield StoryBrowser(self.state.stories, id="story-browser")

            # Main content area
            with Vertical(id="main-content"):
                yield SyncProgressPanel(id="sync-progress-panel")

                with TabbedContent(id="content-tabs"):
                    with TabPane("📝 Details", id="tab-details"):
                        yield StoryDetail(id="story-detail")

                    with TabPane("⚠️ Conflicts", id="tab-conflicts"):
                        yield ConflictPanel(self.state.conflicts, id="conflict-panel")

                    with TabPane("📜 Log", id="tab-log"):
                        self._log_panel = LogPanel(id="log-panel")
                        yield self._log_panel

        # Status bar
        with Horizontal(id="status-bar"):
            mode = "DRY-RUN" if self.state.dry_run else "LIVE"
            yield Static(f"Mode: {mode}", id="status-mode")
            yield Static(" | ", classes="separator")
            file_info = str(self.state.markdown_path) if self.state.markdown_path else "No file"
            yield Static(f"File: {file_info}", id="status-file")
            yield Static(" | ", classes="separator")
            epic_info = self.state.epic_key or "No epic"
            yield Static(f"Epic: {epic_info}", id="status-epic")

        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event."""
        self._log("Dashboard loaded", "success")
        if self.state.stories:
            self._log(f"Loaded {len(self.state.stories)} stories", "info")

    def _log(self, message: str, level: str = "info") -> None:
        """Add a log entry."""
        if self._log_panel:
            self._log_panel.add_entry(message, level)

    @on(StoryBrowser.StorySelected)
    def handle_story_selected(self, event: StoryBrowser.StorySelected) -> None:
        """Handle story selection."""
        self.state.selected_story_id = event.story_id
        story = self.state.get_selected_story()
        detail = self.query_one("#story-detail", StoryDetail)
        detail.update_story(story)
        self._log(f"Selected: {event.story_id}", "info")

    @on(ConflictPanel.ConflictResolved)
    def handle_conflict_resolved(self, event: ConflictPanel.ConflictResolved) -> None:
        """Handle conflict resolution."""
        self._log(f"Conflict resolved with {event.resolution}", "success")

    def action_refresh(self) -> None:
        """Refresh data from file."""
        self._log("Refreshing...", "info")
        if self.state.markdown_path and self.state.markdown_path.exists():
            stories, epic = load_stories_from_file(self.state.markdown_path)
            self.state.stories = stories
            self.state.epic = epic

            # Update widgets
            browser = self.query_one("#story-browser", StoryBrowser)
            browser.update_stories(stories)

            stats = self.query_one("#stats-panel", StatsPanel)
            stats.update_stories(stories)

            self._log(f"Loaded {len(stories)} stories", "success")
        else:
            self._log("No file to refresh", "warning")

    async def action_sync(self) -> None:
        """Start sync operation."""
        self._log("Starting sync...", "info")
        await self._simulate_sync()

    def action_toggle_dry_run(self) -> None:
        """Toggle dry run mode."""
        self.state.dry_run = not self.state.dry_run
        mode = "DRY-RUN" if self.state.dry_run else "LIVE"
        status_mode = self.query_one("#status-mode", Static)
        status_mode.update(f"Mode: {mode}")
        self._log(f"Mode switched to {mode}", "info")

    def action_conflicts(self) -> None:
        """Switch to conflicts tab."""
        tabs = self.query_one("#content-tabs", TabbedContent)
        tabs.active = "tab-conflicts"

    def action_help(self) -> None:
        """Show help."""
        self.app.push_screen(HelpScreen())

    def action_search(self) -> None:
        """Focus search input."""
        # Would normally show a search modal
        self._log("Search: Press / to search stories", "info")

    async def _simulate_sync(self) -> None:
        """Simulate a sync operation with progress updates."""
        progress_panel = self.query_one("#sync-progress-panel", SyncProgressPanel)

        progress = SyncProgress(
            total_operations=len(self.state.stories) * 3,
            phase="analyzing",
            start_time=datetime.now(),
        )
        progress_panel.update_progress(progress)
        self._log("Analyzing stories...", "info")

        await self.app.sleep(0.5)  # type: ignore

        progress.phase = "syncing"
        for i, story in enumerate(self.state.stories):
            progress.completed_operations = i * 3
            progress.current_operation = "Syncing description"
            progress.current_story = str(story.id)
            progress_panel.update_progress(progress)
            self._log(f"Syncing {story.id}: description", "info")
            await self.app.sleep(0.2)  # type: ignore

            progress.completed_operations = i * 3 + 1
            progress.current_operation = "Syncing subtasks"
            progress_panel.update_progress(progress)
            self._log(f"Syncing {story.id}: subtasks", "info")
            await self.app.sleep(0.2)  # type: ignore

            progress.completed_operations = i * 3 + 2
            progress.current_operation = "Syncing status"
            progress_panel.update_progress(progress)
            self._log(f"Syncing {story.id}: status", "info")
            await self.app.sleep(0.1)  # type: ignore

        progress.completed_operations = progress.total_operations
        progress.phase = "complete"
        progress.current_operation = ""
        progress.end_time = datetime.now()
        progress_panel.update_progress(progress)

        mode = "DRY-RUN" if self.state.dry_run else "executed"
        self._log(f"Sync complete ({mode})", "success")


# =============================================================================
# Help Screen
# =============================================================================


class HelpScreen(Screen):
    """Help screen with keyboard shortcuts and usage information."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=True),
        Binding("q", "dismiss", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        yield Header(show_clock=False)

        with Container(id="help-container"):
            yield Static("[bold]Spectra TUI Dashboard - Help[/bold]\n", id="help-title")
            yield Rule()

            help_text = """
[bold]Navigation[/bold]
  ↑/↓       Navigate stories
  Enter     Select story
  Space     Expand/collapse
  Tab       Switch panels

[bold]Actions[/bold]
  s         Start sync
  r         Refresh from file
  d         Toggle dry-run mode
  c         View conflicts

[bold]Search & Filter[/bold]
  /         Search stories
  f         Filter by status
  Escape    Clear search/filter

[bold]General[/bold]
  ?         Show this help
  q         Quit application

[bold]Sync Modes[/bold]
  DRY-RUN   Preview changes without applying
  LIVE      Apply changes to tracker

[bold]Conflict Resolution[/bold]
  When conflicts are detected, use the Conflicts tab to:
  - View local vs remote differences
  - Choose which version to keep
  - Skip conflicts for later
            """
            yield Static(help_text)

            yield Rule()
            yield Static("\n[dim]Press Escape or Q to close[/dim]", id="help-footer")

        yield Footer()

    async def action_dismiss(self, result: None = None) -> None:
        """Dismiss the help screen."""
        self.app.pop_screen()


# =============================================================================
# Main TUI Application
# =============================================================================


class SpectraTUI(App):
    """
    The main Spectra TUI application.

    Provides an interactive terminal dashboard for managing
    epic/story sync operations with real-time feedback.
    """

    TITLE = "Spectra"
    SUB_TITLE = "Interactive Sync Dashboard"
    CSS = SPECTRA_CSS

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]

    def __init__(
        self,
        markdown_path: Path | None = None,
        epic_key: str | None = None,
        dry_run: bool = True,
        demo: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the TUI application.

        Args:
            markdown_path: Path to the markdown file to load.
            epic_key: Epic key for sync operations.
            dry_run: Whether to run in dry-run mode.
            demo: Use demo data for testing.
        """
        super().__init__(*args, **kwargs)

        if demo:
            self.state = create_demo_state()
        else:
            self.state = TUIState(
                markdown_path=markdown_path,
                epic_key=epic_key,
                dry_run=dry_run,
            )

            # Load stories from file if provided
            if markdown_path and markdown_path.exists():
                stories, epic = load_stories_from_file(markdown_path)
                self.state.stories = stories
                self.state.epic = epic
                if epic:
                    self.state.epic_key = str(epic.key)

    def on_mount(self) -> None:
        """Handle application mount."""
        self.push_screen(DashboardScreen(self.state))

    async def sleep(self, seconds: float) -> None:
        """Sleep for the given number of seconds."""
        import asyncio

        await asyncio.sleep(seconds)


# =============================================================================
# Entry Point
# =============================================================================


def run_tui(
    markdown_path: str | None = None,
    epic_key: str | None = None,
    dry_run: bool = True,
    demo: bool = False,
) -> int:
    """
    Run the Spectra TUI application.

    Args:
        markdown_path: Path to markdown file.
        epic_key: Epic key for sync.
        dry_run: Run in dry-run mode.
        demo: Use demo data.

    Returns:
        Exit code (0 for success).
    """
    if not TEXTUAL_AVAILABLE:
        print("Error: Textual is not installed.")
        print("Install with: pip install spectra[tui]")
        return 1

    path = Path(markdown_path) if markdown_path else None
    app = SpectraTUI(
        markdown_path=path,
        epic_key=epic_key,
        dry_run=dry_run,
        demo=demo,
    )
    app.run()
    return 0


def check_textual_available() -> bool:
    """Check if Textual is available."""
    return TEXTUAL_AVAILABLE
