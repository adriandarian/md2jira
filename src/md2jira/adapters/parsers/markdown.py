"""
Markdown Parser - Parse markdown epic files into domain entities.

Implements the DocumentParserPort interface.
"""

import logging
import re
from pathlib import Path
from typing import Optional, Union

from ...core.ports.document_parser import DocumentParserPort, ParserError
from ...core.domain.entities import Epic, UserStory, Subtask
from ...core.domain.value_objects import (
    StoryId,
    IssueKey,
    CommitRef,
    Description,
    AcceptanceCriteria,
)
from ...core.domain.enums import Status, Priority


class MarkdownParser(DocumentParserPort):
    """
    Parser for markdown epic files.
    
    Expected format:
    ### [emoji] US-XXX: Title
    
    | Field | Value |
    |-------|-------|
    | **Story Points** | X |
    | **Priority** | emoji Priority |
    | **Status** | emoji Status |
    
    #### Description
    **As a** role
    **I want** feature
    **So that** benefit
    
    #### Acceptance Criteria
    - [ ] Criterion 1
    
    #### Subtasks
    | # | Subtask | Description | SP | Status |
    
    #### Related Commits
    | Commit | Message |
    """
    
    # Configurable patterns
    STORY_PATTERN = r'### [^\n]+ (US-\d+): ([^\n]+)\n'
    EPIC_TITLE_PATTERN = r'^#\s+[^\n]+\s+([^\n]+)$'
    
    def __init__(self, story_pattern: Optional[str] = None):
        """
        Initialize parser.
        
        Args:
            story_pattern: Optional custom regex for story detection
        """
        self.logger = logging.getLogger("MarkdownParser")
        
        if story_pattern:
            self.STORY_PATTERN = story_pattern
    
    # -------------------------------------------------------------------------
    # DocumentParserPort Implementation
    # -------------------------------------------------------------------------
    
    @property
    def name(self) -> str:
        return "Markdown"
    
    @property
    def supported_extensions(self) -> list[str]:
        return [".md", ".markdown"]
    
    def can_parse(self, source: Union[str, Path]) -> bool:
        if isinstance(source, Path):
            return source.suffix.lower() in self.supported_extensions
        
        # Check if content looks like markdown
        return bool(re.search(self.STORY_PATTERN, source))
    
    def parse_stories(self, source: Union[str, Path]) -> list[UserStory]:
        content = self._get_content(source)
        return self._parse_all_stories(content)
    
    def parse_epic(self, source: Union[str, Path]) -> Optional[Epic]:
        content = self._get_content(source)
        
        # Extract epic title from first heading
        title_match = re.search(r'^#\s+[^\n]*?([A-Z]+-\d+)?.*$', content, re.MULTILINE)
        title = title_match.group(0) if title_match else "Untitled Epic"
        
        # Parse all stories
        stories = self._parse_all_stories(content)
        
        if not stories:
            return None
        
        # Create epic (key will be set when syncing)
        return Epic(
            key=IssueKey("EPIC-0"),  # Placeholder
            title=title.strip("# "),
            stories=stories,
        )
    
    def validate(self, source: Union[str, Path]) -> list[str]:
        content = self._get_content(source)
        errors = []
        
        # Check for story pattern
        story_matches = list(re.finditer(self.STORY_PATTERN, content))
        if not story_matches:
            errors.append("No user stories found matching pattern '### [emoji] US-XXX: Title'")
        
        # Validate each story
        for i, match in enumerate(story_matches):
            story_id = match.group(1)
            start = match.end()
            end = story_matches[i + 1].start() if i + 1 < len(story_matches) else len(content)
            story_content = content[start:end]
            
            # Check for required sections
            if not re.search(r'\*\*Story Points\*\*', story_content):
                errors.append(f"{story_id}: Missing Story Points field")
            
            if not re.search(r'\*\*As a\*\*', story_content):
                errors.append(f"{story_id}: Missing 'As a' description")
        
        return errors
    
    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------
    
    def _get_content(self, source: Union[str, Path]) -> str:
        """Get content from file path or string."""
        if isinstance(source, Path):
            return source.read_text(encoding="utf-8")
        if isinstance(source, str) and Path(source).exists():
            return Path(source).read_text(encoding="utf-8")
        return source
    
    def _parse_all_stories(self, content: str) -> list[UserStory]:
        """Parse all stories from content."""
        stories = []
        
        story_matches = list(re.finditer(self.STORY_PATTERN, content))
        self.logger.debug(f"Found {len(story_matches)} stories")
        
        for i, match in enumerate(story_matches):
            story_id = match.group(1)
            title = match.group(2).strip()
            
            # Get content until next story or end
            start = match.end()
            end = story_matches[i + 1].start() if i + 1 < len(story_matches) else len(content)
            story_content = content[start:end]
            
            try:
                story = self._parse_story(story_id, title, story_content)
                if story:
                    stories.append(story)
            except Exception as e:
                self.logger.warning(f"Failed to parse {story_id}: {e}")
        
        return stories
    
    def _parse_story(
        self,
        story_id: str,
        title: str,
        content: str
    ) -> Optional[UserStory]:
        """Parse a single story from content block."""
        # Extract metadata
        story_points = self._extract_field(content, "Story Points", "0")
        priority = self._extract_field(content, "Priority", "Medium")
        status = self._extract_field(content, "Status", "Planned")
        
        # Extract description
        description = self._extract_description(content)
        
        # Extract acceptance criteria
        acceptance = self._extract_acceptance_criteria(content)
        
        # Extract subtasks
        subtasks = self._extract_subtasks(content)
        
        # Extract commits
        commits = self._extract_commits(content)
        
        # Extract technical notes
        tech_notes = self._extract_technical_notes(content)
        
        return UserStory(
            id=StoryId(story_id),
            title=title,
            description=description,
            acceptance_criteria=acceptance,
            technical_notes=tech_notes,
            story_points=int(story_points) if story_points.isdigit() else 0,
            priority=Priority.from_string(priority),
            status=Status.from_string(status),
            subtasks=subtasks,
            commits=commits,
        )
    
    def _extract_field(
        self,
        content: str,
        field_name: str,
        default: str = ""
    ) -> str:
        """Extract field value from markdown table."""
        pattern = rf'\|\s*\*\*{field_name}\*\*\s*\|\s*([^|]+)\s*\|'
        match = re.search(pattern, content)
        return match.group(1).strip() if match else default
    
    def _extract_description(self, content: str) -> Optional[Description]:
        """Extract As a/I want/So that description."""
        pattern = (
            r'\*\*As a\*\*\s*(.+?)\s*\n\s*'
            r'\*\*I want\*\*\s*(.+?)\s*\n\s*'
            r'\*\*So that\*\*\s*(.+?)(?:\n|$)'
        )
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        return Description(
            role=match.group(1).strip(),
            want=match.group(2).strip(),
            benefit=match.group(3).strip(),
        )
    
    def _extract_acceptance_criteria(self, content: str) -> AcceptanceCriteria:
        """Extract acceptance criteria checkboxes."""
        items = []
        checked = []
        
        section = re.search(
            r'#### Acceptance Criteria\n([\s\S]*?)(?=####|\n---|\Z)',
            content
        )
        
        if section:
            for match in re.finditer(r'- \[([ x])\]\s*(.+)', section.group(1)):
                checked.append(match.group(1).lower() == 'x')
                items.append(match.group(2).strip())
        
        return AcceptanceCriteria.from_list(items, checked)
    
    def _extract_subtasks(self, content: str) -> list[Subtask]:
        """Extract subtasks from table."""
        subtasks = []
        
        section = re.search(
            r'#### Subtasks\n([\s\S]*?)(?=####|\n---|\Z)',
            content
        )
        
        if section:
            # Parse table rows: | # | Subtask | Description | SP | Status |
            pattern = r'\|\s*(\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*(\d+)\s*\|\s*([^|]+)\s*\|'
            
            for match in re.finditer(pattern, section.group(1)):
                subtasks.append(Subtask(
                    number=int(match.group(1)),
                    name=match.group(2).strip(),
                    description=match.group(3).strip(),
                    story_points=int(match.group(4)),
                    status=Status.from_string(match.group(5)),
                ))
        
        return subtasks
    
    def _extract_commits(self, content: str) -> list[CommitRef]:
        """Extract commits from table."""
        commits = []
        
        section = re.search(
            r'#### Related Commits\n([\s\S]*?)(?=####|\n---|\Z)',
            content
        )
        
        if section:
            pattern = r'\|\s*`([^`]+)`\s*\|\s*([^|]+)\s*\|'
            
            for match in re.finditer(pattern, section.group(1)):
                commits.append(CommitRef(
                    hash=match.group(1).strip(),
                    message=match.group(2).strip(),
                ))
        
        return commits
    
    def _extract_technical_notes(self, content: str) -> str:
        """Extract technical notes section."""
        section = re.search(
            r'#### Technical Notes\n([\s\S]*?)(?=####|\Z)',
            content
        )
        
        if section:
            return section.group(1).strip()
        return ""

