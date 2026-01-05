"""
Tolerant Markdown Parsing - Enhanced markdown parsing with precise error reporting.

This module provides utilities for flexible, forgiving markdown parsing that:
1. Tolerates common formatting variants (whitespace, case, etc.)
2. Provides precise parse error locations (line, column, context)
3. Collects warnings for non-critical issues without failing

Usage:
    from spectra.adapters.parsers.tolerant_markdown import (
        TolerantMarkdownParser,
        ParseResult,
        ParseError,
        ParseWarning,
    )

    parser = TolerantMarkdownParser()
    result = parser.parse(content)

    if result.errors:
        for error in result.errors:
            print(f"Error at line {error.line}: {error.message}")

    if result.warnings:
        for warning in result.warnings:
            print(f"Warning at line {warning.line}: {warning.message}")

    stories = result.stories
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from spectra.core.domain.entities import UserStory


class ParseSeverity(Enum):
    """Severity level for parse issues."""

    ERROR = "error"  # Parsing cannot continue or data is corrupt
    WARNING = "warning"  # Parsing can continue, but data may be incomplete
    INFO = "info"  # Informational message about parsing behavior


@dataclass(frozen=True)
class ParseLocation:
    """
    Precise location in the source document.

    Attributes:
        line: 1-indexed line number
        column: 1-indexed column number (optional)
        end_line: End line for multi-line issues (optional)
        end_column: End column for multi-line issues (optional)
        source: Source file path or identifier (optional)
    """

    line: int
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None
    source: str | None = None

    def __str__(self) -> str:
        """Format location for display."""
        parts = []
        if self.source:
            parts.append(self.source)
        if self.column:
            parts.append(f"line {self.line}, column {self.column}")
        else:
            parts.append(f"line {self.line}")
        return ":".join(parts) if self.source else parts[0]


@dataclass(frozen=True)
class ParseIssue:
    """
    Base class for parse errors and warnings.

    Attributes:
        message: Human-readable description of the issue
        location: Location in the source document
        severity: Error severity level
        context: Surrounding text for context (optional)
        suggestion: How to fix the issue (optional)
        code: Error code for programmatic handling (optional)
    """

    message: str
    location: ParseLocation
    severity: ParseSeverity
    context: str | None = None
    suggestion: str | None = None
    code: str | None = None

    @property
    def line(self) -> int:
        """Get the line number for convenience."""
        return self.location.line

    @property
    def column(self) -> int | None:
        """Get the column number for convenience."""
        return self.location.column

    def __str__(self) -> str:
        """Format issue for display."""
        parts = [f"[{self.severity.value.upper()}] {self.location}: {self.message}"]
        if self.context:
            parts.append(f"  Context: {self.context}")
        if self.suggestion:
            parts.append(f"  Suggestion: {self.suggestion}")
        return "\n".join(parts)


@dataclass(frozen=True)
class ParseErrorInfo(ParseIssue):
    """A parse error that may prevent successful parsing."""

    severity: ParseSeverity = field(default=ParseSeverity.ERROR, init=False)


@dataclass(frozen=True)
class ParseWarning(ParseIssue):
    """A parse warning for non-critical issues."""

    severity: ParseSeverity = field(default=ParseSeverity.WARNING, init=False)


@dataclass
class ParseResult:
    """
    Result of parsing with stories, errors, and warnings.

    Attributes:
        stories: Successfully parsed user stories
        errors: Parse errors (may cause data loss)
        warnings: Parse warnings (parsing succeeded with caveats)
        source: Source file path or content identifier
    """

    stories: list[UserStory] = field(default_factory=list)
    errors: list[ParseErrorInfo] = field(default_factory=list)
    warnings: list[ParseWarning] = field(default_factory=list)
    source: str | None = None

    @property
    def success(self) -> bool:
        """Check if parsing was successful (no errors)."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


# =============================================================================
# Tolerant Pattern Matchers
# =============================================================================


class TolerantPatterns:
    """
    Tolerant regex patterns that handle common formatting variants.

    Each pattern is designed to be forgiving of:
    - Extra whitespace
    - Missing/extra newlines
    - Case variations
    - Alternative formatting
    """

    # Story header patterns - tolerant of whitespace, emoji, case
    # Matches: ### US-001: Title, ### ✅ PROJ-123: Title, ###US-001:Title
    STORY_HEADER = re.compile(
        r"^#{2,4}\s*"  # 2-4 hashes with optional space
        r"(?:[^\n]*?\s)?"  # Optional prefix (emoji, status)
        r"([A-Z]+[-_/]\d+|#\d+)"  # Story ID (flexible separators)
        r"\s*:\s*"  # Colon with flexible whitespace
        r"([^\n]+?)"  # Title
        r"\s*$",  # Trailing whitespace
        re.MULTILINE | re.IGNORECASE,
    )

    # Standalone h1 story - tolerant version
    STORY_HEADER_H1 = re.compile(
        r"^#\s*"  # Single hash
        r"(?:[^\n]*?\s)?"  # Optional prefix
        r"([A-Z]+[-_/]\d+|#?\d+)"  # Story ID (more flexible for h1)
        r"\s*:\s*"  # Colon
        r"([^\n]+?)"  # Title
        r"(?:\s*[✅🔲🟡⏸️🔄📋]+)?"  # Optional trailing emoji
        r"\s*$",
        re.MULTILINE | re.IGNORECASE,
    )

    # Field extraction - tolerant of formatting variations
    # Table format: | **Field** | Value | or |**Field**|Value|
    TABLE_FIELD = re.compile(r"\|\s*\*?\*?{field}\*?\*?\s*\|\s*([^|]+?)\s*\|", re.IGNORECASE)

    # Inline format: **Field**: Value or **Field** : Value
    INLINE_FIELD = re.compile(
        r"(?<!>)\s*\*\*{field}\*\*\s*:\s*(.+?)(?:\s*$|\s{{2,}}|\n)", re.MULTILINE | re.IGNORECASE
    )

    # Blockquote format: > **Field**: Value
    BLOCKQUOTE_FIELD = re.compile(
        r">\s*\*\*{field}\*\*\s*:\s*(.+?)(?:\s*$)", re.MULTILINE | re.IGNORECASE
    )

    # Acceptance criteria - various checkbox formats
    # Matches: - [ ] Item, - [x] Item, * [ ] Item, - [] Item, -[ ] Item
    CHECKBOX = re.compile(r"^[\s]*[-*+]\s*\[([xX\s]?)\]\s*(.+?)$", re.MULTILINE)

    # Section headers - tolerant of level and formatting
    # Matches: #### Section, ### Section, ## Section, ####Section
    SECTION_HEADER = re.compile(r"^(#{2,4})\s*{section}\s*$", re.MULTILINE | re.IGNORECASE)

    # Description pattern - flexible "As a/I want/So that"
    DESCRIPTION_FULL = re.compile(
        r"\*\*As\s+a\*\*\s*(.+?)"  # As a [role]
        r"(?:,?\s*\n\s*(?:>\s*)?)?"  # Optional newline with blockquote
        r"\*\*I\s+want\*\*\s*(.+?)"  # I want [feature]
        r"(?:,?\s*\n\s*(?:>\s*)?)?"  # Optional newline with blockquote
        r"\*\*So\s+that\*\*\s*(.+?)$",  # So that [benefit]
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )

    # Alternative description formats (single line, lenient)
    DESCRIPTION_SINGLE_LINE = re.compile(
        r"\*\*As\s+a\*\*\s*([^,\n]+)"
        r"[,\s]+"
        r"\*\*I\s+want\*\*\s*([^,\n]+)"
        r"[,\s]+"
        r"\*\*So\s+that\*\*\s*([^.\n]+)",
        re.IGNORECASE,
    )

    @classmethod
    def field_pattern(cls, field_name: str, format_type: str = "all") -> re.Pattern[str]:
        """
        Create a pattern for extracting a specific field.

        Args:
            field_name: Name of the field to match
            format_type: 'table', 'inline', 'blockquote', or 'all'

        Returns:
            Compiled regex pattern
        """
        # Escape special regex chars but allow flexible spacing
        field_escaped = re.escape(field_name)
        # Allow optional spaces in field name (e.g., "Story Points" or "Story  Points")
        field_pattern = field_escaped.replace(r"\ ", r"\s+")

        if format_type == "table":
            return re.compile(
                rf"\|\s*\*?\*?{field_pattern}\*?\*?\s*\|\s*([^|]+?)\s*\|",
                re.IGNORECASE,
            )
        if format_type == "inline":
            return re.compile(
                rf"(?<!>)\s*\*\*{field_pattern}\*\*\s*:\s*(.+?)(?:\s*$|\s{{2,}}|\n)",
                re.MULTILINE | re.IGNORECASE,
            )
        if format_type == "blockquote":
            return re.compile(
                rf">\s*\*\*{field_pattern}\*\*\s*:\s*(.+?)(?:\s*$)",
                re.MULTILINE | re.IGNORECASE,
            )
        # All formats combined
        return re.compile(
            rf"(?:"
            rf"\|\s*\*?\*?{field_pattern}\*?\*?\s*\|\s*([^|]+?)\s*\|"
            rf"|"
            rf"(?<!>)\s*\*\*{field_pattern}\*\*\s*:\s*(.+?)(?:\s*$|\s{{2,}}|\n)"
            rf"|"
            rf">\s*\*\*{field_pattern}\*\*\s*:\s*(.+?)(?:\s*$)"
            rf")",
            re.MULTILINE | re.IGNORECASE,
        )

    @classmethod
    def section_pattern(cls, section_name: str, levels: str = "2-4") -> re.Pattern[str]:
        """
        Create a pattern for matching a section header.

        Args:
            section_name: Name of the section (e.g., "Acceptance Criteria")
            levels: Header level range (e.g., "2-4" for ##-####) - currently unused

        Returns:
            Compiled regex pattern matching the section and capturing content
        """
        _ = levels  # Reserved for future use
        section_escaped = re.escape(section_name)
        # Allow flexible spacing and optional plural
        section_pattern = section_escaped.replace(r"\ ", r"\s+")

        return re.compile(
            rf"^(#{{2,4}})\s*{section_pattern}\s*\n([\s\S]*?)(?=^#{{2,4}}\s|\n---|\Z)",
            re.MULTILINE | re.IGNORECASE,
        )


# =============================================================================
# Line/Position Utilities
# =============================================================================


def get_line_number(content: str, position: int) -> int:
    """
    Get the 1-indexed line number for a character position.

    Args:
        content: Full text content
        position: Character position (0-indexed)

    Returns:
        1-indexed line number
    """
    return content[:position].count("\n") + 1


def get_column_number(content: str, position: int) -> int:
    """
    Get the 1-indexed column number for a character position.

    Args:
        content: Full text content
        position: Character position (0-indexed)

    Returns:
        1-indexed column number
    """
    line_start = content.rfind("\n", 0, position) + 1
    return position - line_start + 1


def get_line_content(content: str, line_number: int) -> str:
    """
    Get the content of a specific line.

    Args:
        content: Full text content
        line_number: 1-indexed line number

    Returns:
        Content of the specified line (without newline)
    """
    lines = content.split("\n")
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1]
    return ""


def get_context_lines(content: str, line_number: int, before: int = 1, after: int = 1) -> str:
    """
    Get surrounding lines for context.

    Args:
        content: Full text content
        line_number: 1-indexed line number
        before: Number of lines before
        after: Number of lines after

    Returns:
        Formatted context string with line numbers
    """
    lines = content.split("\n")
    start = max(0, line_number - 1 - before)
    end = min(len(lines), line_number + after)

    context_lines = []
    for i in range(start, end):
        prefix = ">" if i == line_number - 1 else " "
        context_lines.append(f"{prefix} {i + 1}: {lines[i]}")

    return "\n".join(context_lines)


def location_from_match(
    content: str, match: re.Match[str], source: str | None = None
) -> ParseLocation:
    """
    Create a ParseLocation from a regex match.

    Args:
        content: Full text content
        match: Regex match object
        source: Source file path (optional)

    Returns:
        ParseLocation with line and column info
    """
    start = match.start()
    end = match.end()
    return ParseLocation(
        line=get_line_number(content, start),
        column=get_column_number(content, start),
        end_line=get_line_number(content, end),
        end_column=get_column_number(content, end),
        source=source,
    )


# =============================================================================
# Tolerant Field Extraction
# =============================================================================


class TolerantFieldExtractor:
    """
    Extract fields from markdown content with tolerance for formatting variants.

    Handles:
    - Multiple format styles (table, inline, blockquote)
    - Case-insensitive field names
    - Field name aliases (Story Points / Points)
    - Extra/missing whitespace
    """

    # Field aliases for common variations
    FIELD_ALIASES: dict[str, list[str]] = {
        "Story Points": ["Points", "SP", "Estimate", "Story Point"],
        "Priority": ["Prio", "P"],
        "Status": ["State"],
        "Story ID": ["ID", "Issue ID"],
    }

    def __init__(self, content: str, source: str | None = None):
        """
        Initialize extractor with content.

        Args:
            content: Markdown content to extract from
            source: Source file path for error reporting
        """
        self.content = content
        self.source = source
        self.warnings: list[ParseWarning] = []

    def extract_field(
        self,
        field_name: str,
        default: str = "",
        required: bool = False,
    ) -> tuple[str, ParseLocation | None]:
        """
        Extract a field value with tolerance for variants.

        Args:
            field_name: Primary field name to look for
            default: Default value if not found
            required: Whether to add warning if not found

        Returns:
            Tuple of (value, location) where location is None if not found
        """
        # Get all variants of the field name
        variants = [field_name, *self.FIELD_ALIASES.get(field_name, [])]

        for variant in variants:
            # Try table format
            pattern = TolerantPatterns.field_pattern(variant, "table")
            match = pattern.search(self.content)
            if match:
                value = self._clean_field_value(match.group(1))
                location = location_from_match(self.content, match, self.source)
                if variant != field_name:
                    self._add_alias_warning(variant, field_name, location)
                return value, location

            # Try inline format
            pattern = TolerantPatterns.field_pattern(variant, "inline")
            match = pattern.search(self.content)
            if match:
                value = self._clean_field_value(match.group(1))
                location = location_from_match(self.content, match, self.source)
                if variant != field_name:
                    self._add_alias_warning(variant, field_name, location)
                return value, location

            # Try blockquote format
            pattern = TolerantPatterns.field_pattern(variant, "blockquote")
            match = pattern.search(self.content)
            if match:
                value = self._clean_field_value(match.group(1))
                location = location_from_match(self.content, match, self.source)
                if variant != field_name:
                    self._add_alias_warning(variant, field_name, location)
                return value, location

        # Not found
        if required:
            self.warnings.append(
                ParseWarning(
                    message=f"Missing field '{field_name}'",
                    location=ParseLocation(line=1, source=self.source),
                    suggestion=f"Add **{field_name}**: <value> or a table row with the field",
                    code="MISSING_FIELD",
                )
            )

        return default, None

    def _clean_field_value(self, value: str) -> str:
        """Clean and normalize a field value."""
        # Remove leading/trailing whitespace
        value = value.strip()
        # Remove trailing punctuation that might be noise
        value = value.rstrip(",;")
        # Normalize internal whitespace
        return " ".join(value.split())

    def _add_alias_warning(self, alias: str, canonical: str, location: ParseLocation) -> None:
        """Add warning about using an alias instead of canonical name."""
        self.warnings.append(
            ParseWarning(
                message=f"Field '{alias}' is an alias for '{canonical}'",
                location=location,
                suggestion=f"Consider using '{canonical}' for consistency",
                code="FIELD_ALIAS",
            )
        )


# =============================================================================
# Tolerant Section Extraction
# =============================================================================


class TolerantSectionExtractor:
    """
    Extract sections from markdown with tolerance for header level variations.

    Handles:
    - Different header levels (##, ###, ####)
    - Case-insensitive section names
    - Plural/singular variations
    """

    # Section name aliases
    SECTION_ALIASES: dict[str, list[str]] = {
        "Acceptance Criteria": ["AC", "Acceptance Criterion", "Criteria"],
        "Subtasks": ["Subtask", "Tasks", "Task List", "Sub Tasks"],
        "Description": ["User Story", "Story"],
        "Technical Notes": ["Tech Notes", "Notes", "Implementation Notes"],
        "Comments": ["Comment", "Discussion"],
        "Dependencies": ["Dependency", "Depends On", "Blocked By"],
        "Related Commits": ["Commits", "Git Commits"],
        "Links": ["Related Issues", "Related"],
    }

    def __init__(self, content: str, source: str | None = None):
        """
        Initialize extractor with content.

        Args:
            content: Markdown content to extract from
            source: Source file path for error reporting
        """
        self.content = content
        self.source = source
        self.warnings: list[ParseWarning] = []

    def extract_section(
        self,
        section_name: str,
        required: bool = False,
    ) -> tuple[str, ParseLocation | None]:
        """
        Extract a section's content with tolerance for variants.

        Args:
            section_name: Primary section name to look for
            required: Whether to add warning if not found

        Returns:
            Tuple of (content, location) where both are None if not found
        """
        variants = [section_name, *self.SECTION_ALIASES.get(section_name, [])]

        for variant in variants:
            pattern = TolerantPatterns.section_pattern(variant)
            match = pattern.search(self.content)
            if match:
                section_content = match.group(2).strip()
                location = location_from_match(self.content, match, self.source)
                if variant != section_name:
                    self._add_alias_warning(variant, section_name, location)
                return section_content, location

        if required:
            self.warnings.append(
                ParseWarning(
                    message=f"Missing section '{section_name}'",
                    location=ParseLocation(line=1, source=self.source),
                    suggestion=f"Add a section header: #### {section_name}",
                    code="MISSING_SECTION",
                )
            )

        return "", None

    def _add_alias_warning(self, alias: str, canonical: str, location: ParseLocation) -> None:
        """Add warning about using an alias instead of canonical name."""
        self.warnings.append(
            ParseWarning(
                message=f"Section '{alias}' is an alias for '{canonical}'",
                location=location,
                suggestion=f"Consider using '#### {canonical}' for consistency",
                code="SECTION_ALIAS",
            )
        )


# =============================================================================
# Tolerant Checkbox Parsing
# =============================================================================


def parse_checkboxes_tolerant(
    content: str,
    source: str | None = None,
) -> tuple[list[tuple[str, bool]], list[ParseWarning]]:
    """
    Parse checkboxes with tolerance for formatting variants.

    Handles:
    - [ ] and [x] and [X] (standard)
    - [] (empty, treated as unchecked)
    - -[ ] (no space after dash)
    - * [ ] (asterisk instead of dash)
    - + [ ] (plus instead of dash)

    Args:
        content: Content containing checkboxes
        source: Source file for error reporting

    Returns:
        Tuple of (items, warnings) where items is list of (text, checked) tuples
    """
    items: list[tuple[str, bool]] = []
    warnings: list[ParseWarning] = []

    # More lenient pattern for checkbox detection
    lenient_pattern = re.compile(r"^[\s]*[-*+]\s*\[([xX\s]?)\]\s*(.+?)$", re.MULTILINE)

    for match in lenient_pattern.finditer(content):
        checkbox_char = match.group(1).strip().lower()
        text = match.group(2).strip()
        checked = checkbox_char == "x"

        items.append((text, checked))

        # Warn about non-standard formatting
        full_match = match.group(0)
        if "* [" in full_match:
            location = location_from_match(content, match, source)
            warnings.append(
                ParseWarning(
                    message="Non-standard checkbox format (using * instead of -)",
                    location=location,
                    suggestion="Use '- [ ]' or '- [x]' for checkboxes",
                    code="NONSTANDARD_CHECKBOX",
                )
            )
        elif "[]" in full_match:
            location = location_from_match(content, match, source)
            warnings.append(
                ParseWarning(
                    message="Empty checkbox marker '[]', treating as unchecked",
                    location=location,
                    suggestion="Use '- [ ]' for unchecked items",
                    code="EMPTY_CHECKBOX",
                )
            )

    return items, warnings


# =============================================================================
# Inline Subtask Parsing (Checkboxes as Subtasks)
# =============================================================================


@dataclass
class InlineSubtaskInfo:
    """
    Information about a subtask parsed from an inline checkbox.

    Attributes:
        name: The subtask name/title
        checked: Whether the checkbox is checked
        description: Optional description extracted from the line
        line_number: Line number in the source document
        story_points: Estimated story points (default 1)
    """

    name: str
    checked: bool
    description: str = ""
    line_number: int = 0
    story_points: int = 1


def parse_inline_subtasks(
    content: str,
    source: str | None = None,
) -> tuple[list[InlineSubtaskInfo], list[ParseWarning]]:
    """
    Parse checkboxes as inline subtasks with tolerance for formatting variants.

    This function extracts subtask information from markdown checkbox lists.
    It supports various checkbox formats and extracts additional metadata
    when available (e.g., story points in parentheses).

    Supported formats:
    - [ ] Task name
    - [x] Completed task
    - [ ] Task name (2 SP)
    - [ ] Task name - description text
    - [ ] Task name: description text
    - [ ] **Task name** with bold formatting
    - [ ] `Task name` with code formatting

    Args:
        content: Content containing checkbox subtasks
        source: Source file for error reporting

    Returns:
        Tuple of (subtasks, warnings) where subtasks is list of InlineSubtaskInfo

    Examples:
        >>> content = '''
        ... - [ ] Implement feature
        ... - [x] Write tests (3 SP)
        ... - [ ] Update docs - Add API reference
        ... '''
        >>> subtasks, warnings = parse_inline_subtasks(content)
        >>> len(subtasks)
        3
        >>> subtasks[0].name
        'Implement feature'
        >>> subtasks[1].checked
        True
        >>> subtasks[1].story_points
        3
    """
    subtasks: list[InlineSubtaskInfo] = []
    warnings: list[ParseWarning] = []

    # Pattern for checkbox detection with optional metadata
    # Matches: - [ ] name, - [x] name, * [ ] name, + [ ] name
    checkbox_pattern = re.compile(
        r"^[\s]*[-*+]\s*\[([xX\s]?)\]\s*(.+?)$",
        re.MULTILINE,
    )

    # Pattern to extract story points from text like "(2 SP)" or "(3 points)"
    sp_pattern = re.compile(
        r"\s*\((\d+)\s*(?:SP|sp|pts?|points?|story\s*points?)\)\s*$",
        re.IGNORECASE,
    )

    # Pattern to extract description after separator (- or :)
    desc_pattern = re.compile(
        r"^(.+?)(?:\s*[-–—:]\s+(.+))?$",
    )

    for match in checkbox_pattern.finditer(content):
        checkbox_char = match.group(1).strip().lower()
        full_text = match.group(2).strip()
        checked = checkbox_char == "x"
        line_number = get_line_number(content, match.start())

        # Extract story points if present
        story_points = 1
        sp_match = sp_pattern.search(full_text)
        if sp_match:
            story_points = int(sp_match.group(1))
            full_text = full_text[: sp_match.start()].strip()

        # Remove markdown formatting (bold, code, etc.)
        name = full_text
        name = re.sub(r"\*\*(.+?)\*\*", r"\1", name)  # Remove bold
        name = re.sub(r"\*(.+?)\*", r"\1", name)  # Remove italic
        name = re.sub(r"`(.+?)`", r"\1", name)  # Remove code
        name = re.sub(r"~~(.+?)~~", r"\1", name)  # Remove strikethrough

        # Extract description if separator found
        description = ""
        desc_match = desc_pattern.match(name)
        if desc_match and desc_match.group(2):
            name = desc_match.group(1).strip()
            description = desc_match.group(2).strip()

        # Skip empty or very short names
        if len(name) < 2:
            location = location_from_match(content, match, source)
            warnings.append(
                ParseWarning(
                    message=f"Skipped checkbox with very short name: '{name}'",
                    location=location,
                    suggestion="Provide a descriptive subtask name",
                    code="SHORT_SUBTASK_NAME",
                )
            )
            continue

        subtasks.append(
            InlineSubtaskInfo(
                name=name,
                checked=checked,
                description=description,
                line_number=line_number,
                story_points=story_points,
            )
        )

        # Warn about non-standard formatting
        original = match.group(0)
        if "* [" in original or "+ [" in original:
            location = location_from_match(content, match, source)
            warnings.append(
                ParseWarning(
                    message="Non-standard checkbox format for subtask",
                    location=location,
                    suggestion="Use '- [ ]' or '- [x]' for subtask checkboxes",
                    code="NONSTANDARD_SUBTASK_CHECKBOX",
                )
            )

    return subtasks, warnings


# =============================================================================
# Tolerant Description Parsing
# =============================================================================


def parse_description_tolerant(
    content: str,
    source: str | None = None,
) -> tuple[dict[str, str] | None, list[ParseWarning]]:
    """
    Parse user story description with tolerance for formatting variants.

    Handles:
    - Multi-line with newlines between parts
    - Single-line comma-separated
    - Blockquote format
    - Missing commas/periods
    - Case variations in keywords

    Args:
        content: Content containing description
        source: Source file for error reporting

    Returns:
        Tuple of (description_dict, warnings) where dict has role/want/benefit keys
    """
    warnings: list[ParseWarning] = []

    # Try full multi-line pattern first
    match = TolerantPatterns.DESCRIPTION_FULL.search(content)
    if match:
        return {
            "role": _clean_description_part(match.group(1)),
            "want": _clean_description_part(match.group(2)),
            "benefit": _clean_description_part(match.group(3)),
        }, warnings

    # Try single-line pattern
    match = TolerantPatterns.DESCRIPTION_SINGLE_LINE.search(content)
    if match:
        return {
            "role": _clean_description_part(match.group(1)),
            "want": _clean_description_part(match.group(2)),
            "benefit": _clean_description_part(match.group(3)),
        }, warnings

    # Try very lenient pattern for blockquotes
    lenient_blockquote = re.compile(
        r">\s*\*\*As\s+a\*\*\s*([^,\n]+)"
        r"[\s\S]*?"
        r"\*\*I\s+want\*\*\s*([^,\n]+)"
        r"[\s\S]*?"
        r"\*\*So\s+that\*\*\s*([^.\n]+)",
        re.IGNORECASE,
    )
    match = lenient_blockquote.search(content)
    if match:
        return {
            "role": _clean_description_part(match.group(1)),
            "want": _clean_description_part(match.group(2)),
            "benefit": _clean_description_part(match.group(3)),
        }, warnings

    # Try partial matches with warnings
    partial_parts: dict[str, str] = {}

    # Look for individual parts
    as_a_match = re.search(r"\*\*As\s+a\*\*\s*([^,\n*]+)", content, re.IGNORECASE)
    if as_a_match:
        partial_parts["role"] = _clean_description_part(as_a_match.group(1))

    i_want_match = re.search(r"\*\*I\s+want\*\*\s*([^,\n*]+)", content, re.IGNORECASE)
    if i_want_match:
        partial_parts["want"] = _clean_description_part(i_want_match.group(1))

    so_that_match = re.search(r"\*\*So\s+that\*\*\s*([^,.\n*]+)", content, re.IGNORECASE)
    if so_that_match:
        partial_parts["benefit"] = _clean_description_part(so_that_match.group(1))

    if partial_parts:
        missing = [k for k in ["role", "want", "benefit"] if k not in partial_parts]
        if missing:
            warnings.append(
                ParseWarning(
                    message=f"Incomplete description: missing {', '.join(missing)}",
                    location=ParseLocation(line=1, source=source),
                    suggestion="Use format: **As a** [role] **I want** [feature] **So that** [benefit]",
                    code="INCOMPLETE_DESCRIPTION",
                )
            )
        return partial_parts, warnings

    return None, warnings


def _clean_description_part(text: str) -> str:
    """Clean a description part (role/want/benefit)."""
    # Remove trailing punctuation and whitespace
    text = text.strip().rstrip(",.")
    # Remove leading/trailing quotes
    text = text.strip("'\"")
    # Normalize whitespace
    return " ".join(text.split())


# =============================================================================
# Error Code Definitions
# =============================================================================


class ParseErrorCode:
    """Standard error codes for parse issues."""

    # Structure errors
    NO_STORIES = "E001"
    INVALID_HEADER = "E002"
    MISSING_REQUIRED_FIELD = "E003"
    DUPLICATE_STORY_ID = "E004"

    # Field errors
    INVALID_FIELD_VALUE = "E101"
    INVALID_STORY_POINTS = "E102"
    INVALID_PRIORITY = "E103"
    INVALID_STATUS = "E104"

    # Format warnings
    FIELD_ALIAS = "W001"
    SECTION_ALIAS = "W002"
    NONSTANDARD_FORMAT = "W003"
    MISSING_OPTIONAL_FIELD = "W004"
    INCOMPLETE_DESCRIPTION = "W005"
    EMPTY_CHECKBOX = "W006"
    NONSTANDARD_CHECKBOX = "W007"
    SHORT_SUBTASK_NAME = "W008"
    NONSTANDARD_SUBTASK_CHECKBOX = "W009"


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Error codes
    "ParseErrorCode",
    # Core types
    "InlineSubtaskInfo",
    "ParseErrorInfo",
    "ParseIssue",
    "ParseLocation",
    "ParseResult",
    "ParseSeverity",
    "ParseWarning",
    # Extractors
    "TolerantFieldExtractor",
    # Patterns
    "TolerantPatterns",
    "TolerantSectionExtractor",
    # Utilities
    "get_column_number",
    "get_context_lines",
    "get_line_content",
    "get_line_number",
    "location_from_match",
    "parse_checkboxes_tolerant",
    "parse_description_tolerant",
    "parse_inline_subtasks",
]
