"""
Domain Events - Things that happened in the domain.

Events are immutable records of something that occurred.
They enable loose coupling and audit trails.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from .value_objects import StoryId, IssueKey


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""
    
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def event_type(self) -> str:
        """Get the event type name."""
        return self.__class__.__name__


@dataclass(frozen=True)
class StoryMatched(DomainEvent):
    """Event: A markdown story was matched to a Jira issue."""
    
    story_id: StoryId = None
    issue_key: IssueKey = None
    match_confidence: float = 1.0  # 0.0 to 1.0
    match_method: str = "title"  # title, id, manual


@dataclass(frozen=True)
class StoryUpdated(DomainEvent):
    """Event: A story's description was updated."""
    
    issue_key: IssueKey = None
    field_name: str = ""
    old_value: Optional[str] = None
    new_value: Optional[str] = None


@dataclass(frozen=True)
class SubtaskCreated(DomainEvent):
    """Event: A new subtask was created."""
    
    parent_key: IssueKey = None
    subtask_key: IssueKey = None
    subtask_name: str = ""
    story_points: int = 0


@dataclass(frozen=True)
class SubtaskUpdated(DomainEvent):
    """Event: A subtask was updated."""
    
    subtask_key: IssueKey = None
    changes: dict = field(default_factory=dict)


@dataclass(frozen=True)
class StatusTransitioned(DomainEvent):
    """Event: An issue's status changed."""
    
    issue_key: IssueKey = None
    from_status: str = ""
    to_status: str = ""
    transition_id: Optional[str] = None


@dataclass(frozen=True)
class CommentAdded(DomainEvent):
    """Event: A comment was added to an issue."""
    
    issue_key: IssueKey = None
    comment_type: str = "text"  # text, commits
    commit_count: int = 0


@dataclass(frozen=True)
class SyncStarted(DomainEvent):
    """Event: A sync operation started."""
    
    epic_key: IssueKey = None
    markdown_path: str = ""
    dry_run: bool = True


@dataclass(frozen=True)
class SyncCompleted(DomainEvent):
    """Event: A sync operation completed."""
    
    epic_key: IssueKey = None
    stories_matched: int = 0
    stories_updated: int = 0
    subtasks_created: int = 0
    comments_added: int = 0
    errors: list = field(default_factory=list)


class EventBus:
    """
    Simple event bus for publishing and subscribing to domain events.
    
    This enables loose coupling between components.
    """
    
    def __init__(self):
        self._handlers: dict[type, list] = {}
        self._history: list[DomainEvent] = []
    
    def subscribe(self, event_type: type, handler: callable) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribers."""
        self._history.append(event)
        
        # Call specific handlers
        for handler in self._handlers.get(type(event), []):
            handler(event)
        
        # Call catch-all handlers
        for handler in self._handlers.get(DomainEvent, []):
            handler(event)
    
    def get_history(self) -> list[DomainEvent]:
        """Get all published events."""
        return self._history.copy()
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()

