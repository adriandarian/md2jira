"""
Jira Adapter - Implements IssueTrackerPort for Atlassian Jira.

This is the main entry point for Jira integration.
"""

import logging
from typing import Any, Optional

from ...core.ports.issue_tracker import (
    IssueTrackerPort,
    IssueData,
    IssueTrackerError,
    TransitionError,
)
from ...core.ports.config_provider import TrackerConfig
from ...core.domain.entities import UserStory, Subtask
from ...core.domain.value_objects import CommitRef
from ..formatters.adf import ADFFormatter
from .client import JiraApiClient


class JiraAdapter(IssueTrackerPort):
    """
    Jira implementation of the IssueTrackerPort.
    
    Translates between domain entities and Jira's API.
    """
    
    # Default Jira field IDs (can be overridden)
    STORY_POINTS_FIELD = "customfield_10014"
    
    # Workflow transitions (varies by project)
    DEFAULT_TRANSITIONS = {
        "Analyze": {"to_open": "7"},
        "Open": {"to_in_progress": "4", "to_resolved": "5"},
        "In Progress": {"to_resolved": "5", "to_open": "301"},
    }
    
    def __init__(
        self,
        config: TrackerConfig,
        dry_run: bool = True,
        formatter: Optional[ADFFormatter] = None,
    ):
        """
        Initialize the Jira adapter.
        
        Args:
            config: Tracker configuration
            dry_run: If True, don't make changes
            formatter: Optional custom ADF formatter
        """
        self.config = config
        self._dry_run = dry_run
        self.formatter = formatter or ADFFormatter()
        self.logger = logging.getLogger("JiraAdapter")
        
        self._client = JiraApiClient(
            base_url=config.url,
            email=config.email,
            api_token=config.api_token,
            dry_run=dry_run,
        )
        
        if config.story_points_field:
            self.STORY_POINTS_FIELD = config.story_points_field
    
    # -------------------------------------------------------------------------
    # IssueTrackerPort Implementation - Properties
    # -------------------------------------------------------------------------
    
    @property
    def name(self) -> str:
        return "Jira"
    
    @property
    def is_connected(self) -> bool:
        return self._client.is_connected
    
    def test_connection(self) -> bool:
        return self._client.test_connection()
    
    # -------------------------------------------------------------------------
    # IssueTrackerPort Implementation - Read Operations
    # -------------------------------------------------------------------------
    
    def get_current_user(self) -> dict[str, Any]:
        return self._client.get_myself()
    
    def get_issue(self, issue_key: str) -> IssueData:
        data = self._client.get(
            f"issue/{issue_key}",
            params={"fields": "summary,description,status,issuetype,subtasks"}
        )
        return self._parse_issue(data)
    
    def get_epic_children(self, epic_key: str) -> list[IssueData]:
        jql = f'parent = {epic_key} ORDER BY key ASC'
        data = self._client.search_jql(
            jql,
            ["summary", "description", "status", "issuetype", "subtasks"]
        )
        
        return [
            self._parse_issue(issue)
            for issue in data.get("issues", [])
        ]
    
    def get_issue_comments(self, issue_key: str) -> list[dict]:
        data = self._client.get(f"issue/{issue_key}/comment")
        return data.get("comments", [])
    
    def get_issue_status(self, issue_key: str) -> str:
        data = self._client.get(
            f"issue/{issue_key}",
            params={"fields": "status"}
        )
        return data["fields"]["status"]["name"]
    
    def search_issues(self, query: str, max_results: int = 50) -> list[IssueData]:
        data = self._client.search_jql(
            query,
            ["summary", "description", "status", "issuetype"],
            max_results=max_results
        )
        return [self._parse_issue(issue) for issue in data.get("issues", [])]
    
    # -------------------------------------------------------------------------
    # IssueTrackerPort Implementation - Write Operations
    # -------------------------------------------------------------------------
    
    def update_issue_description(
        self,
        issue_key: str,
        description: Any
    ) -> bool:
        if self._dry_run:
            self.logger.info(f"[DRY-RUN] Would update description for {issue_key}")
            return True
        
        # Convert to ADF if string
        if isinstance(description, str):
            description = self.formatter.format_text(description)
        
        self._client.put(
            f"issue/{issue_key}",
            json={"fields": {"description": description}}
        )
        self.logger.info(f"Updated description for {issue_key}")
        return True
    
    def create_subtask(
        self,
        parent_key: str,
        summary: str,
        description: Any,
        project_key: str,
        story_points: Optional[int] = None,
        assignee: Optional[str] = None,
    ) -> Optional[str]:
        if self._dry_run:
            self.logger.info(f"[DRY-RUN] Would create subtask '{summary[:50]}...' under {parent_key}")
            return None
        
        # Get current user if no assignee
        if assignee is None:
            assignee = self._client.get_current_user_id()
        
        # Convert description to ADF if string
        if isinstance(description, str):
            description = self.formatter.format_text(description)
        
        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "parent": {"key": parent_key},
            "summary": summary[:255],
            "description": description,
            "issuetype": {"name": "Sub-task"},
            "assignee": {"accountId": assignee},
        }
        
        if story_points is not None:
            fields[self.STORY_POINTS_FIELD] = float(story_points)
        
        result = self._client.post("issue", json={"fields": fields})
        new_key = result.get("key")
        
        if new_key:
            self.logger.info(f"Created subtask {new_key} under {parent_key}")
        
        return new_key
    
    def update_subtask(
        self,
        issue_key: str,
        description: Optional[Any] = None,
        story_points: Optional[int] = None,
        assignee: Optional[str] = None,
    ) -> bool:
        if self._dry_run:
            self.logger.info(f"[DRY-RUN] Would update subtask {issue_key}")
            return True
        
        fields: dict[str, Any] = {}
        
        if description is not None:
            if isinstance(description, str):
                description = self.formatter.format_text(description)
            fields["description"] = description
        
        if story_points is not None:
            fields[self.STORY_POINTS_FIELD] = float(story_points)
        
        if assignee is not None:
            fields["assignee"] = {"accountId": assignee}
        
        if fields:
            self._client.put(f"issue/{issue_key}", json={"fields": fields})
            self.logger.info(f"Updated subtask {issue_key}")
        
        return True
    
    def add_comment(self, issue_key: str, body: Any) -> bool:
        if self._dry_run:
            self.logger.info(f"[DRY-RUN] Would add comment to {issue_key}")
            return True
        
        if isinstance(body, str):
            body = self.formatter.format_text(body)
        
        self._client.post(
            f"issue/{issue_key}/comment",
            json={"body": body}
        )
        self.logger.info(f"Added comment to {issue_key}")
        return True
    
    def transition_issue(self, issue_key: str, target_status: str) -> bool:
        if self._dry_run:
            self.logger.info(f"[DRY-RUN] Would transition {issue_key} to {target_status}")
            return True
        
        current = self.get_issue_status(issue_key)
        if current.lower() == target_status.lower():
            return True
        
        # Get transition path
        target_lower = target_status.lower()
        
        if "resolved" in target_lower or "done" in target_lower:
            path = [
                ("Analyze", "7", None),
                ("Open", "4", None),
                ("In Progress", "5", "Done"),
            ]
        elif "progress" in target_lower:
            path = [
                ("Analyze", "7", None),
                ("Open", "4", None),
            ]
        elif "open" in target_lower:
            path = [("Analyze", "7", None)]
        else:
            self.logger.warning(f"Unknown target status: {target_status}")
            return False
        
        # Execute transitions
        for from_status, transition_id, resolution in path:
            current = self.get_issue_status(issue_key)
            if current == from_status:
                if not self._do_transition(issue_key, transition_id, resolution):
                    return False
        
        # Verify final status
        final = self.get_issue_status(issue_key)
        return target_lower in final.lower()
    
    def _do_transition(
        self,
        issue_key: str,
        transition_id: str,
        resolution: Optional[str] = None
    ) -> bool:
        """Execute a single transition."""
        payload: dict[str, Any] = {"transition": {"id": transition_id}}
        
        if resolution:
            payload["fields"] = {"resolution": {"name": resolution}}
        
        try:
            self._client.post(f"issue/{issue_key}/transitions", json=payload)
            return True
        except IssueTrackerError as e:
            self.logger.error(f"Transition failed: {e}")
            return False
    
    # -------------------------------------------------------------------------
    # IssueTrackerPort Implementation - Utility
    # -------------------------------------------------------------------------
    
    def get_available_transitions(self, issue_key: str) -> list[dict]:
        data = self._client.get(f"issue/{issue_key}/transitions")
        return data.get("transitions", [])
    
    def format_description(self, markdown: str) -> Any:
        return self.formatter.format_text(markdown)
    
    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------
    
    def _parse_issue(self, data: dict) -> IssueData:
        """Parse Jira API response into IssueData."""
        fields = data.get("fields", {})
        
        subtasks = []
        for st in fields.get("subtasks", []):
            subtasks.append(IssueData(
                key=st["key"],
                summary=st["fields"]["summary"],
                status=st["fields"]["status"]["name"],
                issue_type="Sub-task",
            ))
        
        return IssueData(
            key=data["key"],
            summary=fields.get("summary", ""),
            description=fields.get("description"),
            status=fields.get("status", {}).get("name", ""),
            issue_type=fields.get("issuetype", {}).get("name", ""),
            subtasks=subtasks,
        )
    
    # -------------------------------------------------------------------------
    # Extended Methods (Jira-specific)
    # -------------------------------------------------------------------------
    
    def add_commits_comment(
        self,
        issue_key: str,
        commits: list[CommitRef]
    ) -> bool:
        """Add a formatted commits table as a comment."""
        if self._dry_run:
            self.logger.info(f"[DRY-RUN] Would add commits comment to {issue_key}")
            return True
        
        adf = self.formatter.format_commits_table(commits)
        return self.add_comment(issue_key, adf)
    
    def get_subtask_details(self, issue_key: str) -> dict[str, Any]:
        """Get full details of a subtask."""
        data = self._client.get(
            f"issue/{issue_key}",
            params={"fields": f"summary,description,assignee,status,{self.STORY_POINTS_FIELD}"}
        )
        
        fields = data.get("fields", {})
        return {
            "key": data["key"],
            "summary": fields.get("summary", ""),
            "description": fields.get("description"),
            "assignee": fields.get("assignee"),
            "story_points": fields.get(self.STORY_POINTS_FIELD),
            "status": fields.get("status", {}).get("name", ""),
        }

