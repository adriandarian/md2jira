"""
Ports - Abstract interfaces for external dependencies.

Ports define the contracts that adapters must implement.
This enables dependency inversion and easy testing.
"""

from .issue_tracker import IssueTrackerPort, IssueTrackerError
from .document_parser import DocumentParserPort, ParserError
from .document_formatter import DocumentFormatterPort
from .config_provider import ConfigProviderPort

__all__ = [
    "IssueTrackerPort",
    "IssueTrackerError",
    "DocumentParserPort",
    "ParserError",
    "DocumentFormatterPort",
    "ConfigProviderPort",
]

