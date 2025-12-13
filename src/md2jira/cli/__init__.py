"""
CLI Module - Command Line Interface for md2jira.
"""

from .app import main, run
from .exit_codes import ExitCode
from .interactive import InteractiveSession, run_interactive
from .completions import get_completion_script, SUPPORTED_SHELLS
from .logging import (
    JSONFormatter,
    TextFormatter,
    ContextLogger,
    setup_logging,
    get_logger,
)

__all__ = [
    "main",
    "run",
    "ExitCode",
    "InteractiveSession",
    "run_interactive",
    "get_completion_script",
    "SUPPORTED_SHELLS",
    # Logging
    "JSONFormatter",
    "TextFormatter",
    "ContextLogger",
    "setup_logging",
    "get_logger",
]

