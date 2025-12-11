"""
Domain module - Core entities and value objects.

These are pure Python classes with no external dependencies.
They represent the core business concepts of the application.
"""

from .entities import Epic, UserStory, Subtask, Comment
from .value_objects import (
    StoryId,
    IssueKey,
    CommitRef,
    Description,
    AcceptanceCriteria,
)
from .enums import Status, Priority, IssueType
from .events import DomainEvent, StoryMatched, StoryUpdated, SubtaskCreated

__all__ = [
    # Entities
    "Epic",
    "UserStory",
    "Subtask",
    "Comment",
    # Value Objects
    "StoryId",
    "IssueKey",
    "CommitRef",
    "Description",
    "AcceptanceCriteria",
    # Enums
    "Status",
    "Priority",
    "IssueType",
    # Events
    "DomainEvent",
    "StoryMatched",
    "StoryUpdated",
    "SubtaskCreated",
]

