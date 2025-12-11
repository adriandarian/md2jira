"""
Value Objects - Immutable objects defined by their attributes.

Value objects are compared by value, not identity.
They should be immutable and self-validating.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class StoryId:
    """
    Unique identifier for a story within a markdown document.
    
    Format: US-XXX (e.g., US-001, US-042)
    """
    
    value: str
    
    def __post_init__(self) -> None:
        if not re.match(r"^US-\d{3,}$", self.value):
            # Allow flexible formats but normalize
            pass
    
    @classmethod
    def from_string(cls, value: str) -> StoryId:
        """Parse a story ID from string."""
        value = value.strip().upper()
        if not value.startswith("US-"):
            value = f"US-{value}"
        return cls(value)
    
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
    author: Optional[str] = None
    
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
    def from_markdown(cls, text: str) -> Optional[Description]:
        """Parse description from markdown format."""
        pattern = r'\*\*As a\*\*\s*(.+?)\s*\n\s*\*\*I want\*\*\s*(.+?)\s*\n\s*\*\*So that\*\*\s*(.+?)(?:\n|$)'
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
            object.__setattr__(
                self, 
                "checked", 
                tuple([False] * len(self.items))
            )
    
    @classmethod
    def from_list(cls, items: list[str], checked: Optional[list[bool]] = None) -> AcceptanceCriteria:
        """Create from list of items."""
        return cls(
            items=tuple(items),
            checked=tuple(checked) if checked else tuple([False] * len(items)),
        )
    
    def to_markdown(self) -> str:
        """Convert to markdown checkbox format."""
        lines = []
        for item, is_checked in zip(self.items, self.checked):
            checkbox = "[x]" if is_checked else "[ ]"
            lines.append(f"- {checkbox} {item}")
        return "\n".join(lines)
    
    def __len__(self) -> int:
        return len(self.items)
    
    def __iter__(self):
        return iter(zip(self.items, self.checked))
    
    @property
    def completion_ratio(self) -> float:
        """Get ratio of completed criteria."""
        if not self.items:
            return 1.0
        return sum(self.checked) / len(self.items)

