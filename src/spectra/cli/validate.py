"""
Validate - Comprehensive markdown validation for spectra.

Provides detailed validation of markdown epic files with:
- Errors (blocking issues that must be fixed)
- Warnings (potential issues that should be reviewed)
- Suggestions (improvements that could be made)
- Line numbers for easy navigation
- Actionable fix suggestions
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .exit_codes import ExitCode
from .output import Colors, Console, Symbols


class IssueSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"  # Must be fixed
    WARNING = "warning"  # Should be reviewed
    INFO = "info"  # Suggestion/best practice


@dataclass
class ValidationIssue:
    """
    A single validation issue found in the document.

    Attributes:
        severity: Issue severity (error, warning, info).
        code: Unique issue code for reference.
        message: Human-readable description.
        line: Line number where the issue occurs (1-indexed).
        story_id: Story ID if issue is within a story.
        suggestion: Optional fix suggestion.
    """

    severity: IssueSeverity
    code: str
    message: str
    line: int | None = None
    story_id: str | None = None
    suggestion: str | None = None

    @property
    def location(self) -> str:
        """Get formatted location string."""
        parts = []
        if self.line:
            parts.append(f"line {self.line}")
        if self.story_id:
            parts.append(self.story_id)
        return ": ".join(parts) if parts else ""


@dataclass
class ValidationResult:
    """
    Complete validation result.

    Attributes:
        valid: Whether the document passed validation (no errors).
        issues: List of all validation issues.
        stats: Document statistics.
    """

    valid: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)
    file_path: str = ""

    # Statistics
    story_count: int = 0
    subtask_count: int = 0
    total_story_points: int = 0

    @property
    def errors(self) -> list[ValidationIssue]:
        """Get all errors."""
        return [i for i in self.issues if i.severity == IssueSeverity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Get all warnings."""
        return [i for i in self.issues if i.severity == IssueSeverity.WARNING]

    @property
    def infos(self) -> list[ValidationIssue]:
        """Get all info messages."""
        return [i for i in self.issues if i.severity == IssueSeverity.INFO]

    def add_error(
        self,
        code: str,
        message: str,
        line: int | None = None,
        story_id: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add an error (makes document invalid)."""
        self.valid = False
        self.issues.append(
            ValidationIssue(
                severity=IssueSeverity.ERROR,
                code=code,
                message=message,
                line=line,
                story_id=story_id,
                suggestion=suggestion,
            )
        )

    def add_warning(
        self,
        code: str,
        message: str,
        line: int | None = None,
        story_id: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add a warning (document may still be valid)."""
        self.issues.append(
            ValidationIssue(
                severity=IssueSeverity.WARNING,
                code=code,
                message=message,
                line=line,
                story_id=story_id,
                suggestion=suggestion,
            )
        )

    def add_info(
        self,
        code: str,
        message: str,
        line: int | None = None,
        story_id: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add an info message."""
        self.issues.append(
            ValidationIssue(
                severity=IssueSeverity.INFO,
                code=code,
                message=message,
                line=line,
                story_id=story_id,
                suggestion=suggestion,
            )
        )


class MarkdownValidator:
    """
    Comprehensive markdown validator for epic documents.

    Performs extensive checks on markdown structure, content,
    and best practices.
    """

    # Valid status values (case-insensitive)
    VALID_STATUSES = {
        "to do",
        "todo",
        "planned",
        "backlog",
        "open",
        "in progress",
        "in development",
        "in review",
        "active",
        "done",
        "closed",
        "resolved",
        "complete",
        "completed",
        "blocked",
        "on hold",
        "waiting",
        "ready",
        "ready for dev",
        "ready for review",
    }

    # Valid priority values (case-insensitive)
    VALID_PRIORITIES = {
        "highest",
        "high",
        "medium",
        "low",
        "lowest",
        "critical",
        "major",
        "minor",
        "trivial",
        "p0",
        "p1",
        "p2",
        "p3",
        "p4",
        "blocker",
    }

    # Story pattern - matches ### [emoji] US-001: Title or ### [emoji] PROJ-123: Title
    STORY_PATTERN = re.compile(
        r"^###\s+(?:[^\s:]+\s+)?"  # Optional emoji/icon (any non-space chars)
        r"(US-\d+|[A-Z]+-\d+):\s*(.+)$",
        re.MULTILINE,
    )

    # Subtask pattern
    SUBTASK_PATTERN = re.compile(r"^[-*]\s+\[([ xX])\]\s+(.+)$", re.MULTILINE)

    def __init__(self, strict: bool = False):
        """
        Initialize the validator.

        Args:
            strict: If True, treat warnings as errors.
        """
        self.strict = strict

    def validate(self, source: str | Path) -> ValidationResult:
        """
        Validate a markdown file or content.

        Args:
            source: File path or content string.

        Returns:
            ValidationResult with all issues found.
        """
        result = ValidationResult()

        # Get content
        try:
            if isinstance(source, Path):
                content = source.read_text(encoding="utf-8")
                result.file_path = str(source)
            elif isinstance(source, str):
                # Check if it looks like content (has newlines or markdown) vs a file path
                # A file path typically doesn't have newlines and doesn't start with #
                is_likely_content = "\n" in source or source.startswith("#")
                if not is_likely_content and Path(source).exists():
                    content = Path(source).read_text(encoding="utf-8")
                    result.file_path = source
                else:
                    content = source
                    result.file_path = "<string>"
            else:
                content = str(source)
                result.file_path = "<string>"
        except FileNotFoundError:
            result.add_error(
                "E001",
                f"File not found: {source}",
                suggestion="Check the file path is correct",
            )
            return result
        except Exception as e:
            result.add_error(
                "E002",
                f"Cannot read file: {e}",
            )
            return result

        # Build line mapping
        lines = content.split("\n")

        # Run all validation checks
        self._check_structure(content, lines, result)
        self._check_stories(content, lines, result)
        self._check_best_practices(content, lines, result)

        # If strict mode, convert warnings to errors
        if self.strict:
            for issue in result.issues:
                if issue.severity == IssueSeverity.WARNING:
                    issue.severity = IssueSeverity.ERROR
                    result.valid = False

        return result

    # -------------------------------------------------------------------------
    # Structure Checks
    # -------------------------------------------------------------------------

    def _check_structure(
        self,
        content: str,
        lines: list[str],
        result: ValidationResult,
    ) -> None:
        """Check overall document structure."""

        # Check for stories
        story_matches = list(self.STORY_PATTERN.finditer(content))

        if not story_matches:
            result.add_error(
                "E100",
                "No user stories found",
                suggestion="Add stories with format: ### US-001: Story Title",
            )
            return

        result.story_count = len(story_matches)

        # Check for duplicate story IDs
        [m.group(1) for m in story_matches]
        seen_ids: dict[str, int] = {}

        for match in story_matches:
            story_id = match.group(1)
            line_num = content[: match.start()].count("\n") + 1

            if story_id in seen_ids:
                result.add_error(
                    "E101",
                    f"Duplicate story ID: {story_id}",
                    line=line_num,
                    story_id=story_id,
                    suggestion=f"First occurrence at line {seen_ids[story_id]}. Use unique IDs.",
                )
            else:
                seen_ids[story_id] = line_num

        # Check for story separators
        separator_count = content.count("\n---\n")
        if separator_count < len(story_matches) - 1:
            result.add_warning(
                "W100",
                "Missing story separators (---)",
                suggestion="Add '---' between stories for better readability",
            )

    # -------------------------------------------------------------------------
    # Story Checks
    # -------------------------------------------------------------------------

    def _check_stories(
        self,
        content: str,
        lines: list[str],
        result: ValidationResult,
    ) -> None:
        """Check individual stories."""
        story_matches = list(self.STORY_PATTERN.finditer(content))

        total_points = 0
        total_subtasks = 0

        for i, match in enumerate(story_matches):
            story_id = match.group(1)
            story_title = match.group(2).strip()
            story_start = match.start()
            story_line = content[:story_start].count("\n") + 1

            # Get story content (until next story or end)
            story_end = story_matches[i + 1].start() if i + 1 < len(story_matches) else len(content)

            story_content = content[story_start:story_end]

            # Check title
            if len(story_title) < 5:
                result.add_warning(
                    "W200",
                    "Story title is very short",
                    line=story_line,
                    story_id=story_id,
                    suggestion="Use descriptive titles that explain what the story does",
                )

            if len(story_title) > 100:
                result.add_warning(
                    "W201",
                    "Story title is very long",
                    line=story_line,
                    story_id=story_id,
                    suggestion="Consider shortening the title and adding details to description",
                )

            # Check story points
            points_match = re.search(
                r"\*\*Story\s*Points\*\*\s*\|\s*(\d+|[^\|]+)", story_content, re.IGNORECASE
            )

            if not points_match:
                result.add_warning(
                    "W202",
                    "Missing Story Points",
                    line=story_line,
                    story_id=story_id,
                    suggestion="Add a metadata table with | **Story Points** | 3 |",
                )
            else:
                points_value = points_match.group(1).strip()
                if points_value.isdigit():
                    total_points += int(points_value)
                elif points_value not in ("TBD", "?", "-", "N/A"):
                    result.add_warning(
                        "W203",
                        f"Invalid story points value: '{points_value}'",
                        line=story_line,
                        story_id=story_id,
                        suggestion="Story points should be a number or 'TBD'",
                    )

            # Check status
            status_match = re.search(
                r"\*\*Status\*\*\s*\|\s*(?:[\U0001F300-\U0001F9FF]\s*)?([^\|]+)",
                story_content,
                re.IGNORECASE,
            )

            if status_match:
                status_value = status_match.group(1).strip().lower()
                # Remove emoji if present
                status_value = re.sub(r"[\U0001F300-\U0001F9FF]", "", status_value).strip()

                if status_value and status_value not in self.VALID_STATUSES:
                    result.add_warning(
                        "W204",
                        f"Unrecognized status: '{status_match.group(1).strip()}'",
                        line=story_line,
                        story_id=story_id,
                        suggestion="Use standard statuses: To Do, In Progress, Done, etc.",
                    )

            # Check priority
            priority_match = re.search(
                r"\*\*Priority\*\*\s*\|\s*(?:[\U0001F300-\U0001F9FF]\s*)?([^\|]+)",
                story_content,
                re.IGNORECASE,
            )

            if priority_match:
                priority_value = priority_match.group(1).strip().lower()
                # Remove emoji if present
                priority_value = re.sub(r"[\U0001F300-\U0001F9FF]", "", priority_value).strip()

                if priority_value and priority_value not in self.VALID_PRIORITIES:
                    result.add_warning(
                        "W205",
                        f"Unrecognized priority: '{priority_match.group(1).strip()}'",
                        line=story_line,
                        story_id=story_id,
                        suggestion="Use standard priorities: High, Medium, Low, etc.",
                    )

            # Check description format
            has_as_a = "**as a**" in story_content.lower()
            has_i_want = "**i want**" in story_content.lower()
            has_so_that = "**so that**" in story_content.lower()

            if not has_as_a and not has_i_want:
                result.add_info(
                    "I200",
                    "Story lacks user story format",
                    line=story_line,
                    story_id=story_id,
                    suggestion="Consider using: **As a** X, **I want** Y, **So that** Z",
                )
            elif has_as_a and has_i_want and not has_so_that:
                result.add_info(
                    "I201",
                    "Story description missing 'So that' (benefit)",
                    line=story_line,
                    story_id=story_id,
                    suggestion="Add **So that** to explain the user benefit",
                )

            # Check for acceptance criteria / subtasks
            subtask_matches = self.SUBTASK_PATTERN.findall(story_content)
            if subtask_matches:
                total_subtasks += len(subtask_matches)
            else:
                result.add_info(
                    "I202",
                    "Story has no subtasks or acceptance criteria",
                    line=story_line,
                    story_id=story_id,
                    suggestion="Add acceptance criteria with: - [ ] Criterion",
                )

        result.subtask_count = total_subtasks
        result.total_story_points = total_points

    # -------------------------------------------------------------------------
    # Best Practice Checks
    # -------------------------------------------------------------------------

    def _check_best_practices(
        self,
        content: str,
        lines: list[str],
        result: ValidationResult,
    ) -> None:
        """Check best practices and common issues."""

        # Check for epic header
        has_epic_header = bool(
            re.search(r"^#\s+.*(?:Epic|🚀)", content, re.MULTILINE | re.IGNORECASE)
        )
        if not has_epic_header:
            result.add_info(
                "I300",
                "No epic header found",
                suggestion="Add an epic header: # 🚀 PROJ-123: Epic Title",
            )

        # Check for very long lines
        for i, line in enumerate(lines):
            if len(line) > 200:
                result.add_info(
                    "I301",
                    f"Line is very long ({len(line)} chars)",
                    line=i + 1,
                    suggestion="Consider breaking into multiple lines for readability",
                )
                break  # Only report once

        # Check for trailing whitespace (common issue)
        trailing_ws_count = sum(1 for line in lines if line.endswith((" ", "\t")))
        if trailing_ws_count > 5:
            result.add_info(
                "I302",
                f"Many lines have trailing whitespace ({trailing_ws_count})",
                suggestion="Trim trailing whitespace for cleaner diffs",
            )

        # Check for consistent story ID format
        story_ids = [m.group(1) for m in self.STORY_PATTERN.finditer(content)]
        if story_ids:
            # Check if mixing formats (US-XXX vs PROJ-XXX)
            us_format = [s for s in story_ids if s.startswith("US-")]
            proj_format = [s for s in story_ids if not s.startswith("US-")]

            if us_format and proj_format:
                result.add_warning(
                    "W300",
                    "Mixing story ID formats (US-XXX and project keys)",
                    suggestion="Use consistent story IDs throughout the document",
                )


def format_validation_result(result: ValidationResult, color: bool = True) -> str:
    """
    Format a validation result for display.

    Args:
        result: ValidationResult to format.
        color: Whether to use ANSI colors.

    Returns:
        Formatted string for display.
    """
    lines: list[str] = []

    # Summary line
    if result.valid:
        if color:
            status = f"{Colors.GREEN}{Colors.BOLD}{Symbols.CHECK} Validation Passed{Colors.RESET}"
        else:
            status = "✓ Validation Passed"
    elif color:
        status = f"{Colors.RED}{Colors.BOLD}{Symbols.CROSS} Validation Failed{Colors.RESET}"
    else:
        status = "✗ Validation Failed"

    lines.append(status)
    lines.append("")

    # File info
    if result.file_path:
        lines.append(f"  File: {result.file_path}")

    # Statistics
    lines.append(f"  Stories: {result.story_count}")
    lines.append(f"  Subtasks: {result.subtask_count}")
    lines.append(f"  Total Story Points: {result.total_story_points}")
    lines.append("")

    # Errors
    if result.errors:
        if color:
            lines.append(f"{Colors.RED}{Colors.BOLD}Errors ({len(result.errors)}):{Colors.RESET}")
        else:
            lines.append(f"Errors ({len(result.errors)}):")

        for issue in result.errors:
            lines.extend(_format_issue(issue, color))
        lines.append("")

    # Warnings
    if result.warnings:
        if color:
            lines.append(
                f"{Colors.YELLOW}{Colors.BOLD}Warnings ({len(result.warnings)}):{Colors.RESET}"
            )
        else:
            lines.append(f"Warnings ({len(result.warnings)}):")

        for issue in result.warnings:
            lines.extend(_format_issue(issue, color))
        lines.append("")

    # Info (only show if verbose or no errors/warnings)
    if result.infos and not result.errors:
        if color:
            lines.append(f"{Colors.CYAN}Suggestions ({len(result.infos)}):{Colors.RESET}")
        else:
            lines.append(f"Suggestions ({len(result.infos)}):")

        for issue in result.infos[:5]:  # Limit to 5
            lines.extend(_format_issue(issue, color))

        if len(result.infos) > 5:
            lines.append(f"  ... and {len(result.infos) - 5} more suggestions")
        lines.append("")

    return "\n".join(lines)


def _format_issue(issue: ValidationIssue, color: bool) -> list[str]:
    """Format a single issue."""
    lines: list[str] = []

    # Icon based on severity
    if issue.severity == IssueSeverity.ERROR:
        icon = f"{Colors.RED}{Symbols.CROSS}{Colors.RESET}" if color else "✗"
        code_color = Colors.RED if color else ""
    elif issue.severity == IssueSeverity.WARNING:
        icon = f"{Colors.YELLOW}{Symbols.WARN}{Colors.RESET}" if color else "⚠"
        code_color = Colors.YELLOW if color else ""
    else:
        icon = f"{Colors.CYAN}{Symbols.INFO}{Colors.RESET}" if color else "ℹ"
        code_color = Colors.CYAN if color else ""

    # Main line
    location = f" ({issue.location})" if issue.location else ""
    if color:
        lines.append(f"  {icon} {code_color}[{issue.code}]{Colors.RESET} {issue.message}{location}")
    else:
        lines.append(f"  {icon} [{issue.code}] {issue.message}{location}")

    # Suggestion
    if issue.suggestion:
        if color:
            lines.append(f"      {Colors.DIM}→ {issue.suggestion}{Colors.RESET}")
        else:
            lines.append(f"      → {issue.suggestion}")

    return lines


def run_validate(
    console: Console,
    markdown_path: str,
    strict: bool = False,
    show_all: bool = False,
    show_guide: bool = False,
    suggest_fix: bool = False,
    auto_fix: bool = False,
    ai_tool: str | None = None,
) -> int:
    """
    Run comprehensive validation on a markdown file.

    Args:
        console: Console for output.
        markdown_path: Path to markdown file.
        strict: Treat warnings as errors.
        show_all: Show all issues including info.
        show_guide: Show the format guide.
        suggest_fix: Show AI prompt for fixing issues.
        auto_fix: Automatically fix using AI tool.
        ai_tool: Specific AI tool to use for auto-fix.

    Returns:
        Exit code.
    """
    from .ai_fix import (
        detect_ai_tools,
        format_fix_suggestion,
        generate_copy_paste_prompt,
        generate_format_guide,
        get_tool_by_name,
        run_ai_fix,
        select_ai_tool,
    )

    console.header(f"spectra Validate {Symbols.CHECK}")

    # Show format guide if requested
    if show_guide:
        guide = generate_format_guide()
        print(guide)
        if not Path(markdown_path).exists():
            return ExitCode.SUCCESS

    # Check file exists
    if not Path(markdown_path).exists():
        console.error_rich(FileNotFoundError(markdown_path))
        return ExitCode.FILE_NOT_FOUND

    console.info(f"File: {markdown_path}")

    if strict:
        console.info("Mode: Strict (warnings are errors)")

    console.print()

    # Run validation
    validator = MarkdownValidator(strict=strict)
    result = validator.validate(markdown_path)

    # Format and display result
    formatted = format_validation_result(result, color=console.color)
    print(formatted)

    # If validation failed or has issues, offer AI assistance
    if not result.valid or result.warnings:
        # Collect error and warning messages
        error_msgs = [f"[{e.code}] {e.message}" for e in result.errors]
        warning_msgs = [f"[{w.code}] {w.message}" for w in result.warnings]

        # Handle suggest-fix: show the prompt for manual copy-paste
        if suggest_fix:
            console.print()
            console.section("AI Fix Prompt")
            console.print()
            prompt = generate_copy_paste_prompt(markdown_path, error_msgs, warning_msgs)
            print(prompt)
            console.print()
            console.info("Copy the prompt above into your AI tool, then paste your file content.")
            console.info("The AI will return a corrected version of your markdown.")
            return ExitCode.VALIDATION_ERROR if not result.valid else ExitCode.SUCCESS

        # Handle auto-fix: run an AI tool to fix the file
        if auto_fix:
            console.print()
            console.section("AI Auto-Fix")

            # Detect available tools
            tools = detect_ai_tools()

            if not tools:
                console.error("No AI CLI tools detected on your system.")
                console.print()
                console.info("Install one of the following:")
                console.info("  • claude (Anthropic): pip install anthropic")
                console.info("  • ollama: https://ollama.ai")
                console.info("  • aider: pip install aider-chat")
                console.info("  • llm: pip install llm")
                return ExitCode.CONFIG_ERROR

            # Select tool
            if ai_tool:
                selected = get_tool_by_name(ai_tool, tools)
                if not selected:
                    console.error(f"AI tool '{ai_tool}' not found or not installed.")
                    console.info("Available tools: " + ", ".join(t.tool.value for t in tools))
                    return ExitCode.CONFIG_ERROR
            else:
                selected = select_ai_tool(tools, console)
                if not selected:
                    console.warning("Cancelled by user")
                    return ExitCode.CANCELLED

            console.info(f"Using {selected.display_name} to fix formatting issues...")
            console.print()

            # Run the fix
            fix_result = run_ai_fix(
                tool=selected,
                file_path=markdown_path,
                errors=error_msgs,
                warnings=warning_msgs,
                dry_run=False,
            )

            if fix_result.success:
                if fix_result.fixed_content:
                    # Write the fixed content back to the file
                    try:
                        Path(markdown_path).write_text(fix_result.fixed_content, encoding="utf-8")
                        console.success("File has been fixed!")
                        console.info("Run validation again to verify: spectra --validate --markdown " + markdown_path)
                    except Exception as e:
                        console.error(f"Failed to write fixed content: {e}")
                        console.print()
                        console.info("Fixed content (copy manually):")
                        print(fix_result.fixed_content[:2000])  # Truncate for display
                        if len(fix_result.fixed_content) > 2000:
                            console.info("... (truncated)")
                elif fix_result.output:
                    console.success("AI processing complete!")
                    console.print()
                    print(fix_result.output)
            else:
                console.error(f"AI fix failed: {fix_result.error}")
                return ExitCode.ERROR

            return ExitCode.SUCCESS

        # If validation failed and no fix options specified, show fix suggestions
        if not result.valid:
            tools = detect_ai_tools()
            suggestion = format_fix_suggestion(
                file_path=markdown_path,
                errors=error_msgs,
                warnings=warning_msgs,
                tools=tools if tools else None,
                color=console.color,
            )
            print(suggestion)

    # Return appropriate exit code
    if not result.valid or (result.warnings and strict):
        return ExitCode.VALIDATION_ERROR
    if result.warnings:
        return ExitCode.SUCCESS  # Warnings don't fail by default
    return ExitCode.SUCCESS
