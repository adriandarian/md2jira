"""
Sync Orchestrator - Coordinates the synchronization process.

This is the main entry point for sync operations.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any, Callable

from ...core.ports.issue_tracker import IssueTrackerPort, IssueData
from ...core.ports.document_parser import DocumentParserPort
from ...core.ports.document_formatter import DocumentFormatterPort
from ...core.ports.config_provider import SyncConfig
from ...core.domain.entities import Epic, UserStory, Subtask
from ...core.domain.events import EventBus, SyncStarted, SyncCompleted
from ..commands import (
    CommandBatch,
    UpdateDescriptionCommand,
    CreateSubtaskCommand,
    UpdateSubtaskCommand,
    AddCommentCommand,
    TransitionStatusCommand,
)


@dataclass
class SyncResult:
    """Result of a sync operation."""
    
    success: bool = True
    dry_run: bool = True
    
    # Counts
    stories_matched: int = 0
    stories_updated: int = 0
    subtasks_created: int = 0
    subtasks_updated: int = 0
    comments_added: int = 0
    statuses_updated: int = 0
    
    # Details
    matched_stories: list[tuple[str, str]] = field(default_factory=list)  # (md_id, jira_key)
    unmatched_stories: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)


class SyncOrchestrator:
    """
    Orchestrates the synchronization between markdown and issue tracker.
    
    Phases:
    1. Parse markdown into domain entities
    2. Fetch current state from issue tracker
    3. Match markdown stories to tracker issues
    4. Generate commands for required changes
    5. Execute commands (or preview in dry-run)
    """
    
    def __init__(
        self,
        tracker: IssueTrackerPort,
        parser: DocumentParserPort,
        formatter: DocumentFormatterPort,
        config: SyncConfig,
        event_bus: Optional[EventBus] = None,
    ):
        """
        Initialize the orchestrator.
        
        Args:
            tracker: Issue tracker port
            parser: Document parser port
            formatter: Document formatter port
            config: Sync configuration
            event_bus: Optional event bus
        """
        self.tracker = tracker
        self.parser = parser
        self.formatter = formatter
        self.config = config
        self.event_bus = event_bus or EventBus()
        self.logger = logging.getLogger("SyncOrchestrator")
        
        self._md_stories: list[UserStory] = []
        self._jira_issues: list[IssueData] = []
        self._matches: dict[str, str] = {}  # story_id -> issue_key
    
    # -------------------------------------------------------------------------
    # Main Entry Points
    # -------------------------------------------------------------------------
    
    def analyze(
        self,
        markdown_path: str,
        epic_key: str,
    ) -> SyncResult:
        """
        Analyze markdown and issue tracker without making changes.
        
        Args:
            markdown_path: Path to markdown file
            epic_key: Jira epic key
            
        Returns:
            SyncResult with analysis details
        """
        result = SyncResult(dry_run=True)
        
        # Parse markdown
        self._md_stories = self.parser.parse_stories(markdown_path)
        self.logger.info(f"Parsed {len(self._md_stories)} stories from markdown")
        
        # Fetch Jira issues
        self._jira_issues = self.tracker.get_epic_children(epic_key)
        self.logger.info(f"Found {len(self._jira_issues)} issues in Jira epic")
        
        # Match stories
        self._match_stories(result)
        
        return result
    
    def sync(
        self,
        markdown_path: str,
        epic_key: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> SyncResult:
        """
        Full sync from markdown to issue tracker.
        
        Args:
            markdown_path: Path to markdown file
            epic_key: Jira epic key
            progress_callback: Optional callback for progress updates
            
        Returns:
            SyncResult with sync details
        """
        result = SyncResult(dry_run=self.config.dry_run)
        
        # Publish start event
        self.event_bus.publish(SyncStarted(
            epic_key=epic_key,
            markdown_path=markdown_path,
            dry_run=self.config.dry_run,
        ))
        
        # Phase 1: Analyze
        self._report_progress(progress_callback, "Analyzing", 1, 5)
        self.analyze(markdown_path, epic_key)
        result.stories_matched = len(self._matches)
        result.matched_stories = list(self._matches.items())
        
        # Phase 2: Update descriptions
        if self.config.sync_descriptions:
            self._report_progress(progress_callback, "Updating descriptions", 2, 5)
            self._sync_descriptions(result)
        
        # Phase 3: Sync subtasks
        if self.config.sync_subtasks:
            self._report_progress(progress_callback, "Syncing subtasks", 3, 5)
            self._sync_subtasks(result)
        
        # Phase 4: Add commit comments
        if self.config.sync_comments:
            self._report_progress(progress_callback, "Adding comments", 4, 5)
            self._sync_comments(result)
        
        # Phase 5: Sync statuses
        if self.config.sync_statuses:
            self._report_progress(progress_callback, "Syncing statuses", 5, 5)
            self._sync_statuses(result)
        
        # Publish complete event
        self.event_bus.publish(SyncCompleted(
            epic_key=epic_key,
            stories_matched=result.stories_matched,
            stories_updated=result.stories_updated,
            subtasks_created=result.subtasks_created,
            comments_added=result.comments_added,
            errors=result.errors,
        ))
        
        return result
    
    def sync_descriptions_only(
        self,
        markdown_path: str,
        epic_key: str,
    ) -> SyncResult:
        """Sync only story descriptions."""
        result = SyncResult(dry_run=self.config.dry_run)
        self.analyze(markdown_path, epic_key)
        self._sync_descriptions(result)
        return result
    
    def sync_subtasks_only(
        self,
        markdown_path: str,
        epic_key: str,
    ) -> SyncResult:
        """Sync only subtasks."""
        result = SyncResult(dry_run=self.config.dry_run)
        self.analyze(markdown_path, epic_key)
        self._sync_subtasks(result)
        return result
    
    def sync_statuses_only(
        self,
        markdown_path: str,
        epic_key: str,
        target_status: str = "Resolved",
    ) -> SyncResult:
        """Sync subtask statuses to target status."""
        result = SyncResult(dry_run=self.config.dry_run)
        self.analyze(markdown_path, epic_key)
        self._sync_statuses(result, target_status)
        return result
    
    # -------------------------------------------------------------------------
    # Matching Logic
    # -------------------------------------------------------------------------
    
    def _match_stories(self, result: SyncResult) -> None:
        """Match markdown stories to Jira issues."""
        self._matches = {}
        
        for md_story in self._md_stories:
            matched_issue = None
            
            # Try to match by title
            for jira_issue in self._jira_issues:
                if md_story.matches_title(jira_issue.summary):
                    matched_issue = jira_issue
                    break
            
            if matched_issue:
                self._matches[str(md_story.id)] = matched_issue.key
                result.matched_stories.append((str(md_story.id), matched_issue.key))
                self.logger.debug(f"Matched {md_story.id} -> {matched_issue.key}")
            else:
                result.unmatched_stories.append(str(md_story.id))
                result.add_warning(f"Could not match story: {md_story.id} - {md_story.title}")
        
        result.stories_matched = len(self._matches)
    
    # -------------------------------------------------------------------------
    # Sync Phases
    # -------------------------------------------------------------------------
    
    def _sync_descriptions(self, result: SyncResult) -> None:
        """Sync story descriptions."""
        batch = CommandBatch(stop_on_error=False)
        
        for md_story in self._md_stories:
            story_id = str(md_story.id)
            if story_id not in self._matches:
                continue
            
            issue_key = self._matches[story_id]
            
            # Only update if story has description
            if md_story.description:
                adf = self.formatter.format_story_description(md_story)
                
                batch.add(UpdateDescriptionCommand(
                    tracker=self.tracker,
                    issue_key=issue_key,
                    description=adf,
                    event_bus=self.event_bus,
                    dry_run=self.config.dry_run,
                ))
        
        # Execute batch
        batch.execute_all()
        result.stories_updated = batch.executed_count
        
        for cmd_result in batch.results:
            if not cmd_result.success:
                result.add_error(cmd_result.error)
    
    def _sync_subtasks(self, result: SyncResult) -> None:
        """Sync subtasks for each story."""
        for md_story in self._md_stories:
            story_id = str(md_story.id)
            if story_id not in self._matches:
                continue
            
            issue_key = self._matches[story_id]
            project_key = issue_key.split("-")[0]
            
            # Get existing subtasks
            jira_issue = self.tracker.get_issue(issue_key)
            existing_subtasks = {st.summary.lower(): st for st in jira_issue.subtasks}
            
            for md_subtask in md_story.subtasks:
                subtask_name_lower = md_subtask.name.lower()
                
                if subtask_name_lower in existing_subtasks:
                    # Update existing subtask
                    existing = existing_subtasks[subtask_name_lower]
                    
                    cmd = UpdateSubtaskCommand(
                        tracker=self.tracker,
                        issue_key=existing.key,
                        description=md_subtask.description,
                        story_points=md_subtask.story_points,
                        event_bus=self.event_bus,
                        dry_run=self.config.dry_run,
                    )
                    cmd_result = cmd.execute()
                    
                    if cmd_result.success and not cmd_result.dry_run:
                        result.subtasks_updated += 1
                else:
                    # Create new subtask
                    adf = self.formatter.format_text(md_subtask.description)
                    
                    cmd = CreateSubtaskCommand(
                        tracker=self.tracker,
                        parent_key=issue_key,
                        project_key=project_key,
                        summary=md_subtask.name,
                        description=adf,
                        story_points=md_subtask.story_points,
                        event_bus=self.event_bus,
                        dry_run=self.config.dry_run,
                    )
                    cmd_result = cmd.execute()
                    
                    if cmd_result.success:
                        result.subtasks_created += 1
                    elif cmd_result.error:
                        result.add_error(cmd_result.error)
    
    def _sync_comments(self, result: SyncResult) -> None:
        """Add commit comments to stories."""
        for md_story in self._md_stories:
            story_id = str(md_story.id)
            if story_id not in self._matches:
                continue
            
            if not md_story.commits:
                continue
            
            issue_key = self._matches[story_id]
            
            # Check if commits comment already exists
            existing_comments = self.tracker.get_issue_comments(issue_key)
            has_commits_comment = any(
                "Related Commits" in str(c.get("body", ""))
                for c in existing_comments
            )
            
            if has_commits_comment:
                continue
            
            # Format commits as table
            adf = self.formatter.format_commits_table(md_story.commits)
            
            cmd = AddCommentCommand(
                tracker=self.tracker,
                issue_key=issue_key,
                body=adf,
                event_bus=self.event_bus,
                dry_run=self.config.dry_run,
            )
            cmd_result = cmd.execute()
            
            if cmd_result.success:
                result.comments_added += 1
            elif cmd_result.error:
                result.add_error(cmd_result.error)
    
    def _sync_statuses(
        self,
        result: SyncResult,
        target_status: str = "Resolved"
    ) -> None:
        """Sync subtask statuses based on markdown status."""
        for md_story in self._md_stories:
            story_id = str(md_story.id)
            if story_id not in self._matches:
                continue
            
            # Only sync done stories
            if not md_story.status.is_complete():
                continue
            
            issue_key = self._matches[story_id]
            jira_issue = self.tracker.get_issue(issue_key)
            
            for jira_subtask in jira_issue.subtasks:
                if jira_subtask.status.lower() in ("resolved", "done", "closed"):
                    continue
                
                cmd = TransitionStatusCommand(
                    tracker=self.tracker,
                    issue_key=jira_subtask.key,
                    target_status=target_status,
                    event_bus=self.event_bus,
                    dry_run=self.config.dry_run,
                )
                cmd_result = cmd.execute()
                
                if cmd_result.success:
                    result.statuses_updated += 1
                elif cmd_result.error:
                    result.add_error(cmd_result.error)
    
    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    
    def _report_progress(
        self,
        callback: Optional[Callable],
        phase: str,
        current: int,
        total: int
    ) -> None:
        """Report progress to callback if provided."""
        if callback:
            callback(phase, current, total)
        self.logger.info(f"Phase {current}/{total}: {phase}")

