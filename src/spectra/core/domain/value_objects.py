"""
Value Objects - Immutable objects defined by their attributes.

Value objects are compared by value, not identity.
They should be immutable and self-validating.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass(frozen=True)
class StoryId:
    """
    Unique identifier for a story within a markdown document.

    Format: PREFIX-NUMBER (e.g., US-001, EU-042, PROJ-123, FEAT-001)

    Accepts any alphanumeric prefix followed by a hyphen and number.
    This allows organizations to use their own naming conventions.
    """

    value: str

    # Pattern for valid story IDs: one or more uppercase letters, hyphen, one or more digits
    PATTERN = re.compile(r"^[A-Z]+-\d+$", re.IGNORECASE)

    def __post_init__(self) -> None:
        # Normalize to uppercase
        normalized = self.value.strip().upper()
        if normalized != self.value:
            object.__setattr__(self, "value", normalized)

    @classmethod
    def from_string(cls, value: str) -> StoryId:
        """Parse a story ID from string.

        Accepts any PREFIX-NUMBER format (e.g., US-001, EU-042, PROJ-123).
        """
        return cls(value.strip().upper())

    @property
    def prefix(self) -> str:
        """Extract the prefix portion (e.g., 'US' from 'US-001')."""
        if "-" in self.value:
            return self.value.split("-")[0]
        return ""

    @property
    def number(self) -> int:
        """Extract the numeric portion."""
        match = re.search(r"\d+", self.value)
        return int(match.group()) if match else 0

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class IssueKey:
    """
    Jira issue key.

    Format: PROJECT-NUMBER (e.g., PROJ-123, UPP-80006)
    """

    value: str

    def __post_init__(self) -> None:
        if not re.match(r"^[A-Z]+-\d+$", self.value.upper()):
            raise ValueError(f"Invalid issue key format: {self.value}")

    @property
    def project(self) -> str:
        """Extract project key."""
        return self.value.split("-")[0].upper()

    @property
    def number(self) -> int:
        """Extract issue number."""
        return int(self.value.split("-")[1])

    def __str__(self) -> str:
        return self.value.upper()


@dataclass(frozen=True)
class CommitRef:
    """Reference to a git commit."""

    hash: str
    message: str
    author: str | None = None

    @property
    def short_hash(self) -> str:
        """Get abbreviated hash (7 chars)."""
        return self.hash[:7]

    def __str__(self) -> str:
        return f"{self.short_hash}: {self.message}"


@dataclass(frozen=True)
class Description:
    """
    User story description in "As a / I want / So that" format.

    Immutable value object representing the story's purpose.
    """

    role: str
    want: str
    benefit: str
    additional_context: str = ""

    @classmethod
    def from_markdown(cls, text: str) -> Description | None:
        """Parse description from markdown format."""
        pattern = r"\*\*As a\*\*\s*(.+?)\s*\n\s*\*\*I want\*\*\s*(.+?)\s*\n\s*\*\*So that\*\*\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if not match:
            return None

        return cls(
            role=match.group(1).strip(),
            want=match.group(2).strip(),
            benefit=match.group(3).strip(),
        )

    def to_markdown(self) -> str:
        """Convert to markdown format."""
        parts = [
            f"**As a** {self.role}",
            f"**I want** {self.want}",
            f"**So that** {self.benefit}",
        ]
        if self.additional_context:
            parts.append(f"\n{self.additional_context}")
        return "\n".join(parts)

    def to_plain_text(self) -> str:
        """Convert to plain text."""
        return f"As a {self.role}, I want {self.want}, so that {self.benefit}"

    def __str__(self) -> str:
        return self.to_plain_text()


@dataclass(frozen=True)
class AcceptanceCriteria:
    """
    Collection of acceptance criteria for a story.

    Each criterion is a checkable item.
    """

    items: tuple[str, ...] = field(default_factory=tuple)
    checked: tuple[bool, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        # Ensure checked matches items length
        if len(self.checked) != len(self.items):
            object.__setattr__(self, "checked", tuple([False] * len(self.items)))

    @classmethod
    def from_list(cls, items: list[str], checked: list[bool] | None = None) -> AcceptanceCriteria:
        """Create from list of items."""
        return cls(
            items=tuple(items),
            checked=tuple(checked) if checked else tuple([False] * len(items)),
        )

    def to_markdown(self) -> str:
        """Convert to markdown checkbox format."""
        lines = []
        for item, is_checked in zip(self.items, self.checked, strict=False):
            checkbox = "[x]" if is_checked else "[ ]"
            lines.append(f"- {checkbox} {item}")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[tuple[str, bool]]:
        return iter(zip(self.items, self.checked, strict=False))

    @property
    def completion_ratio(self) -> float:
        """Get ratio of completed criteria."""
        if not self.items:
            return 1.0
        return sum(self.checked) / len(self.items)
