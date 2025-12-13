"""
Centralized exception hierarchy for md2jira.

This module defines a consistent exception hierarchy for all error conditions
in the application. All custom exceptions inherit from Md2JiraError.

Exception Hierarchy:
    Md2JiraError (base)
    ├── TrackerError (issue tracker operations)
    │   ├── AuthenticationError
    │   ├── ResourceNotFoundError
    │   ├── AccessDeniedError
    │   ├── TransitionError
    │   ├── RateLimitError
    │   └── TransientError
    ├── ParserError (document parsing)
    ├── OutputError (document output/wiki)
    │   ├── AuthenticationError (aliased from TrackerError)
    │   ├── ResourceNotFoundError (aliased from TrackerError)
    │   ├── AccessDeniedError (aliased from TrackerError)
    │   └── RateLimitError (aliased from TrackerError)
    └── ConfigError (configuration)
"""

from typing import Optional


class Md2JiraError(Exception):
    """
    Base exception for all md2jira errors.
    
    All custom exceptions in the application should inherit from this class.
    This allows catching all application errors with a single except clause.
    
    Attributes:
        message: Human-readable error description
        cause: Original exception that caused this error (for chaining)
    """
    
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.cause = cause
    
    def __str__(self) -> str:
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message


# =============================================================================
# Tracker Errors - Issue tracker operations (Jira, GitHub, Linear, etc.)
# =============================================================================

class TrackerError(Md2JiraError):
    """
    Base exception for issue tracker errors.
    
    Raised when operations with issue trackers (Jira, GitHub, Linear, Azure DevOps)
    fail. Subclasses provide more specific error categorization.
    
    Attributes:
        issue_key: The issue key/ID involved in the error (e.g., "PROJ-123")
    """
    
    def __init__(
        self,
        message: str,
        issue_key: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, cause)
        self.issue_key = issue_key


class AuthenticationError(TrackerError):
    """
    Authentication failed.
    
    Raised when API credentials are invalid, expired, or missing.
    This includes API tokens, OAuth tokens, and basic auth credentials.
    """
    pass


class ResourceNotFoundError(TrackerError):
    """
    Requested resource was not found.
    
    Raised when an issue, project, user, or other resource doesn't exist.
    Typically corresponds to HTTP 404 responses.
    
    Note: Named ResourceNotFoundError to avoid confusion with similar exceptions
    in other contexts (e.g., file not found).
    """
    pass


class AccessDeniedError(TrackerError):
    """
    Insufficient permissions for the requested operation.
    
    Raised when the authenticated user lacks permission to perform the action.
    Typically corresponds to HTTP 403 responses.
    
    Note: Named AccessDeniedError instead of PermissionError to avoid
    shadowing Python's built-in PermissionError.
    """
    pass


class TransitionError(TrackerError):
    """
    Failed to transition issue status.
    
    Raised when a status transition is not allowed by the workflow,
    or when the transition doesn't exist.
    """
    pass


class RateLimitError(TrackerError):
    """
    Rate limit exceeded.
    
    Raised when the API rate limit is exceeded. The retry_after attribute
    indicates how many seconds to wait before retrying.
    
    Attributes:
        retry_after: Seconds to wait before retrying (from Retry-After header)
    """
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        issue_key: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, issue_key, cause)
        self.retry_after = retry_after


class TransientError(TrackerError):
    """
    Transient server error that may succeed on retry.
    
    Raised for temporary server errors (5xx HTTP status codes).
    These operations should be retried with exponential backoff.
    """
    pass


# =============================================================================
# Parser Errors - Document parsing operations
# =============================================================================

class ParserError(Md2JiraError):
    """
    Error during document parsing.
    
    Raised when parsing markdown, YAML, or other input formats fails.
    Provides context about where the error occurred.
    
    Attributes:
        line_number: Line number where the error occurred (1-indexed)
        source: Source file path or identifier
    """
    
    def __init__(
        self,
        message: str,
        line_number: Optional[int] = None,
        source: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, cause)
        self.line_number = line_number
        self.source = source
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.source:
            parts.insert(0, f"{self.source}")
        if self.line_number:
            parts.insert(1 if self.source else 0, f"line {self.line_number}")
        if self.cause:
            parts.append(f"(caused by: {self.cause})")
        return ": ".join(parts) if len(parts) > 1 else parts[0]


# =============================================================================
# Output Errors - Document output operations (Confluence, etc.)
# =============================================================================

class OutputError(Md2JiraError):
    """
    Base exception for document output errors.
    
    Raised when operations with documentation systems (Confluence, Notion, etc.)
    fail. Uses the same error types as TrackerError for consistency.
    
    Attributes:
        page_id: The page/document ID involved in the error
    """
    
    def __init__(
        self,
        message: str,
        page_id: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, cause)
        self.page_id = page_id


class OutputAuthenticationError(OutputError):
    """Authentication failed for document output system."""
    pass


class OutputNotFoundError(OutputError):
    """Page or space not found in document output system."""
    pass


class OutputAccessDeniedError(OutputError):
    """Insufficient permissions for document output operation."""
    pass


class OutputRateLimitError(OutputError):
    """Rate limit exceeded for document output system."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        page_id: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, page_id, cause)
        self.retry_after = retry_after


# =============================================================================
# Config Errors - Configuration and settings
# =============================================================================

class ConfigError(Md2JiraError):
    """
    Base exception for configuration errors.
    
    Raised when loading or parsing configuration fails.
    
    Attributes:
        config_path: Path to the configuration file (if applicable)
    """
    
    def __init__(
        self,
        message: str,
        config_path: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, cause)
        self.config_path = config_path
    
    def __str__(self) -> str:
        if self.config_path:
            return f"{self.config_path}: {self.message}"
        return self.message


class ConfigFileError(ConfigError):
    """
    Configuration file parsing failed.
    
    Raised when a YAML, TOML, or other config file cannot be parsed.
    """
    pass


class ConfigValidationError(ConfigError):
    """
    Configuration validation failed.
    
    Raised when configuration values are invalid or missing required fields.
    """
    pass


# =============================================================================
# Backward Compatibility Aliases
# =============================================================================

# These aliases maintain backward compatibility with existing code
# that imports from the old locations. They should be considered
# deprecated and new code should use the canonical names.

# For issue_tracker module compatibility
IssueTrackerError = TrackerError
NotFoundError = ResourceNotFoundError
PermissionError = AccessDeniedError  # Shadows built-in intentionally for compat

# For document_output module compatibility  
DocumentOutputError = OutputError


__all__ = [
    # Base
    "Md2JiraError",
    # Tracker errors (primary names)
    "TrackerError",
    "AuthenticationError",
    "ResourceNotFoundError",
    "AccessDeniedError",
    "TransitionError",
    "RateLimitError",
    "TransientError",
    # Parser errors
    "ParserError",
    # Output errors
    "OutputError",
    "OutputAuthenticationError",
    "OutputNotFoundError",
    "OutputAccessDeniedError",
    "OutputRateLimitError",
    # Config errors
    "ConfigError",
    "ConfigFileError",
    "ConfigValidationError",
    # Backward compatibility aliases
    "IssueTrackerError",
    "NotFoundError",
    "PermissionError",
    "DocumentOutputError",
]

