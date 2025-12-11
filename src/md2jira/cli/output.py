"""
Output - Rich console output formatting.

Provides pretty-printed output with colors and formatting.
"""

import sys
from dataclasses import dataclass
from typing import Optional

from ..application.sync import SyncResult


class Colors:
    """ANSI color codes."""
    
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


class Symbols:
    """Unicode symbols for output."""
    
    CHECK = "✓"
    CROSS = "✗"
    ARROW = "→"
    DOT = "•"
    WARN = "⚠"
    INFO = "ℹ"
    ROCKET = "🚀"
    GEAR = "⚙"
    FILE = "📄"
    FOLDER = "📁"
    LINK = "🔗"
    
    # Box drawing
    BOX_TL = "╭"
    BOX_TR = "╮"
    BOX_BL = "╰"
    BOX_BR = "╯"
    BOX_H = "─"
    BOX_V = "│"


class Console:
    """Console output helper with colors and formatting."""
    
    def __init__(self, color: bool = True, verbose: bool = False):
        self.color = color and sys.stdout.isatty()
        self.verbose = verbose
    
    def _c(self, text: str, *codes: str) -> str:
        """Apply color codes to text."""
        if not self.color:
            return text
        return "".join(codes) + text + Colors.RESET
    
    def print(self, text: str = "") -> None:
        """Print text."""
        print(text)
    
    def header(self, text: str) -> None:
        """Print a header."""
        width = max(len(text) + 4, 50)
        border = Colors.CYAN + Symbols.BOX_H * width + Colors.RESET if self.color else "-" * width
        
        self.print()
        self.print(border)
        self.print(self._c(f"  {text}", Colors.BOLD, Colors.CYAN))
        self.print(border)
        self.print()
    
    def section(self, text: str) -> None:
        """Print a section header."""
        self.print()
        self.print(self._c(f"{Symbols.ARROW} {text}", Colors.BOLD, Colors.BLUE))
    
    def success(self, text: str) -> None:
        """Print success message."""
        self.print(self._c(f"  {Symbols.CHECK} {text}", Colors.GREEN))
    
    def error(self, text: str) -> None:
        """Print error message."""
        self.print(self._c(f"  {Symbols.CROSS} {text}", Colors.RED))
    
    def warning(self, text: str) -> None:
        """Print warning message."""
        self.print(self._c(f"  {Symbols.WARN} {text}", Colors.YELLOW))
    
    def info(self, text: str) -> None:
        """Print info message."""
        self.print(self._c(f"  {Symbols.INFO} {text}", Colors.CYAN))
    
    def detail(self, text: str) -> None:
        """Print detail text (dimmed)."""
        self.print(self._c(f"    {text}", Colors.DIM))
    
    def debug(self, text: str) -> None:
        """Print debug message (only in verbose mode)."""
        if self.verbose:
            self.print(self._c(f"  [DEBUG] {text}", Colors.DIM))
    
    def item(self, text: str, status: Optional[str] = None) -> None:
        """Print a list item."""
        status_str = ""
        if status == "ok":
            status_str = self._c(f" [{Symbols.CHECK}]", Colors.GREEN)
        elif status == "skip":
            status_str = self._c(" [SKIP]", Colors.YELLOW)
        elif status == "fail":
            status_str = self._c(f" [{Symbols.CROSS}]", Colors.RED)
        elif status:
            status_str = self._c(f" [{status}]", Colors.DIM)
        
        self.print(f"    {Symbols.DOT} {text}{status_str}")
    
    def table(self, headers: list[str], rows: list[list[str]]) -> None:
        """Print a simple table."""
        # Calculate column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))
        
        # Print header
        header_line = "  " + "  ".join(
            self._c(h.ljust(widths[i]), Colors.BOLD)
            for i, h in enumerate(headers)
        )
        self.print(header_line)
        self.print("  " + "  ".join("-" * w for w in widths))
        
        # Print rows
        for row in rows:
            row_line = "  " + "  ".join(
                str(cell).ljust(widths[i]) if i < len(widths) else str(cell)
                for i, cell in enumerate(row)
            )
            self.print(row_line)
    
    def progress(self, current: int, total: int, message: str = "") -> None:
        """Print progress bar."""
        width = 30
        filled = int(width * current / total)
        bar = "█" * filled + "░" * (width - filled)
        pct = int(100 * current / total)
        
        line = f"\r  [{bar}] {pct}% {message}"
        sys.stdout.write(line)
        sys.stdout.flush()
        
        if current >= total:
            self.print()
    
    def dry_run_banner(self) -> None:
        """Print dry-run mode banner."""
        self.print()
        banner = f"  {Symbols.GEAR} DRY-RUN MODE - No changes will be made"
        if self.color:
            self.print(f"{Colors.BG_YELLOW}{Colors.BOLD}{banner}{Colors.RESET}")
        else:
            self.print(f"*** {banner} ***")
        self.print()
    
    def sync_result(self, result: SyncResult) -> None:
        """Print sync result summary."""
        self.section("Sync Summary")
        self.print()
        
        if result.dry_run:
            self.info("Mode: DRY-RUN (no changes made)")
        else:
            self.info("Mode: LIVE EXECUTION")
        
        self.print()
        
        # Stats table
        stats = [
            ["Stories Matched", str(result.stories_matched)],
            ["Stories Updated", str(result.stories_updated)],
            ["Subtasks Created", str(result.subtasks_created)],
            ["Subtasks Updated", str(result.subtasks_updated)],
            ["Comments Added", str(result.comments_added)],
            ["Statuses Updated", str(result.statuses_updated)],
        ]
        
        self.table(["Metric", "Count"], stats)
        
        # Warnings
        if result.warnings:
            self.print()
            self.warning(f"{len(result.warnings)} warning(s):")
            for w in result.warnings[:5]:
                self.detail(w)
            if len(result.warnings) > 5:
                self.detail(f"... and {len(result.warnings) - 5} more")
        
        # Errors
        if result.errors:
            self.print()
            self.error(f"{len(result.errors)} error(s):")
            for e in result.errors[:5]:
                self.detail(e)
            if len(result.errors) > 5:
                self.detail(f"... and {len(result.errors) - 5} more")
        
        # Final status
        self.print()
        if result.success:
            self.success("Sync completed successfully!")
        else:
            self.error("Sync completed with errors")
    
    def confirm(self, message: str) -> bool:
        """Ask for confirmation."""
        prompt = self._c(f"\n{Symbols.WARN} {message} (y/N): ", Colors.YELLOW)
        try:
            response = input(prompt).strip().lower()
            return response in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            self.print()
            return False

