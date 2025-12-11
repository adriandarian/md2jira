#!/usr/bin/env python3
"""
md2jira - Markdown to Jira Sync Tool

A CLI tool for synchronizing markdown documentation with Jira.
Supports syncing user stories, subtasks, descriptions, and comments from
markdown files to Jira epics.

Repository: https://github.com/adriandarian/md2jira

Features:
- Dry-run mode by default (use --execute to actually make changes)
- Confirmation prompts before each write operation
- Detailed logging of all actions
- Export current Jira state before modifications
- Sync descriptions with proper formatting (bold, checkboxes, code)
- Sync subtasks with descriptions, assignees, and story points
- Add commit comments to stories
- Sync subtask statuses based on markdown

Usage:
    # Specify markdown file and epic
    python md2jira.py --markdown /path/to/epic.md --epic PROJ-123
    
    # Export current Jira state (always safe)
    python md2jira.py --epic PROJ-123 --export
    
    # Dry-run to see what would happen (default)
    python md2jira.py --markdown epic.md --epic PROJ-123
    
    # Execute changes
    python md2jira.py --markdown epic.md --epic PROJ-123 --execute

Environment Variables Required:
    JIRA_URL: Your Jira instance URL (e.g., https://company.atlassian.net)
    JIRA_EMAIL: Your Jira email
    JIRA_API_TOKEN: Your Jira API token (create at https://id.atlassian.com/manage-profile/security/api-tokens)
"""

import os
import re
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

# Third-party imports - install with: pip install requests
try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests")
    exit(1)


# =============================================================================
# Configuration
# =============================================================================

class Config:
    """Configuration loaded from environment variables and CLI args."""
    
    def __init__(self, markdown_path: str = None, jira_url: str = None):
        self.jira_url = jira_url or os.environ.get("JIRA_URL")
        self.jira_email = os.environ.get("JIRA_EMAIL")
        self.jira_api_token = os.environ.get("JIRA_API_TOKEN")
        self.markdown_path = Path(markdown_path) if markdown_path else None
        
        # Try loading from .env file if env vars not set
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            self._load_env_file(env_file)
        
    def _load_env_file(self, env_file: Path):
        """Load environment variables from .env file."""
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key == "JIRA_EMAIL" and not self.jira_email:
                    self.jira_email = value
                elif key == "JIRA_API_TOKEN" and not self.jira_api_token:
                    self.jira_api_token = value
                elif key == "JIRA_URL" and not self.jira_url:
                    self.jira_url = value
        
    def validate(self, require_markdown: bool = True):
        """Validate required configuration."""
        missing = []
        if not self.jira_url:
            missing.append("JIRA_URL")
        if not self.jira_email:
            missing.append("JIRA_EMAIL")
        if not self.jira_api_token:
            missing.append("JIRA_API_TOKEN")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}\n"
                           f"Set them in .env file or with:\n"
                           f"  export JIRA_URL='https://your-company.atlassian.net'\n"
                           f"  export JIRA_EMAIL='your-email@company.com'\n"
                           f"  export JIRA_API_TOKEN='your-api-token'")
        if require_markdown and self.markdown_path and not self.markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {self.markdown_path}")


# =============================================================================
# Data Models
# =============================================================================

class StoryStatus(Enum):
    DONE = "✅ Done"
    IN_PROGRESS = "🔄 In Progress"
    PLANNED = "📋 Planned"
    
    @classmethod
    def from_string(cls, s: str) -> "StoryStatus":
        s = s.strip()
        for status in cls:
            if status.value in s or s in status.value:
                return status
        # Default mappings
        if "done" in s.lower() or "✅" in s:
            return cls.DONE
        if "progress" in s.lower() or "🔄" in s:
            return cls.IN_PROGRESS
        return cls.PLANNED


class Priority(Enum):
    CRITICAL = "🔴 Critical"
    HIGH = "🟡 High"
    MEDIUM = "🟢 Medium"
    LOW = "🟢 Low"
    
    @classmethod
    def from_string(cls, s: str) -> "Priority":
        s = s.strip().lower()
        if "critical" in s or "🔴" in s:
            return cls.CRITICAL
        if "high" in s or "🟡" in s:
            return cls.HIGH
        if "low" in s:
            return cls.LOW
        return cls.MEDIUM


@dataclass
class Subtask:
    """Represents a subtask within a user story."""
    number: int
    name: str
    description: str
    story_points: int
    status: StoryStatus
    
    def to_jira_description(self) -> str:
        return f"{self.description}\n\nStory Points: {self.story_points}"


@dataclass
class Commit:
    """Represents a related commit."""
    hash: str
    message: str


@dataclass
class UserStory:
    """Represents a user story parsed from the markdown."""
    id: str  # e.g., "US-001"
    title: str
    story_points: int
    priority: Priority
    status: StoryStatus
    description: str
    acceptance_criteria: list[str] = field(default_factory=list)
    subtasks: list[Subtask] = field(default_factory=list)
    commits: list[Commit] = field(default_factory=list)
    technical_notes: str = ""
    
    def to_jira_description(self) -> str:
        """Convert to Jira-compatible description format (markdown)."""
        parts = [self.description]
        
        if self.acceptance_criteria:
            parts.append("\n## Acceptance Criteria\n")
            for ac in self.acceptance_criteria:
                parts.append(f"- [ ] {ac}")
        
        if self.technical_notes:
            parts.append(f"\n## Technical Notes\n{self.technical_notes}")
        
        return "\n".join(parts)
    
    def get_commits_comment(self) -> str:
        """Generate a comment with related commits."""
        if not self.commits:
            return ""
        
        lines = ["h3. Related Commits", ""]
        lines.append("||Commit||Message||")
        for commit in self.commits:
            lines.append(f"|{commit.hash}|{commit.message}|")
        
        return "\n".join(lines)
    
    def normalize_title(self) -> str:
        """Normalize title for matching."""
        title = self.title.lower()
        # Remove common suffixes like "(Future)"
        title = re.sub(r'\s*\(future\)\s*$', '', title)
        # Normalize whitespace and punctuation
        title = re.sub(r'[^\w\s]', ' ', title)
        title = ' '.join(title.split())
        return title


@dataclass
class JiraIssue:
    """Represents an issue fetched from Jira."""
    key: str
    summary: str
    description: Optional[dict]  # ADF format
    status: str
    issue_type: str
    subtasks: list["JiraIssue"] = field(default_factory=list)
    comments: list[dict] = field(default_factory=list)
    
    def normalize_title(self) -> str:
        """Normalize title for matching."""
        title = self.summary.lower()
        # Normalize whitespace and punctuation
        title = re.sub(r'[^\w\s]', ' ', title)
        title = ' '.join(title.split())
        return title
    
    def has_description(self) -> bool:
        """Check if issue has a meaningful description."""
        return bool(self.description)


# =============================================================================
# Markdown Parser
# =============================================================================

class MarkdownEpicParser:
    """Parses a markdown epic file into structured data.
    
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
    - [ ] Criterion 2
    
    #### Subtasks
    | # | Subtask | Description | SP | Status |
    |---|---------|-------------|-----|--------|
    | 1 | Name | Description | 1 | Status |
    
    #### Related Commits
    | Commit | Message |
    |--------|---------|
    | `hash` | Message |
    """
    
    # Configurable patterns
    STORY_PATTERN = r'### [^\n]+ (US-\d+): ([^\n]+)\n'
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.content = filepath.read_text(encoding="utf-8")
        
    def parse(self) -> list[UserStory]:
        """Parse all user stories from the markdown file."""
        stories = []
        
        story_matches = list(re.finditer(self.STORY_PATTERN, self.content))
        
        for i, match in enumerate(story_matches):
            story_id = match.group(1)
            title = match.group(2).strip()
            
            # Get content until next story or end
            start = match.end()
            end = story_matches[i + 1].start() if i + 1 < len(story_matches) else len(self.content)
            story_content = self.content[start:end]
            
            story = self._parse_story(story_id, title, story_content)
            if story:
                stories.append(story)
        
        return stories
    
    def _parse_story(self, story_id: str, title: str, content: str) -> Optional[UserStory]:
        """Parse a single user story from its content block."""
        try:
            # Extract metadata from table
            story_points = self._extract_field(content, "Story Points", default="0")
            priority = self._extract_field(content, "Priority", default="Medium")
            status = self._extract_field(content, "Status", default="Planned")
            
            # Extract description (As a... I want... So that...)
            description = self._extract_description(content)
            
            # Extract acceptance criteria
            acceptance_criteria = self._extract_acceptance_criteria(content)
            
            # Extract subtasks
            subtasks = self._extract_subtasks(content)
            
            # Extract commits
            commits = self._extract_commits(content)
            
            # Extract technical notes
            technical_notes = self._extract_technical_notes(content)
            
            return UserStory(
                id=story_id,
                title=title,
                story_points=int(story_points) if story_points.isdigit() else 0,
                priority=Priority.from_string(priority),
                status=StoryStatus.from_string(status),
                description=description,
                acceptance_criteria=acceptance_criteria,
                subtasks=subtasks,
                commits=commits,
                technical_notes=technical_notes,
            )
        except Exception as e:
            logging.warning(f"Failed to parse story {story_id}: {e}")
            return None
    
    def _extract_field(self, content: str, field_name: str, default: str = "") -> str:
        """Extract a field value from a markdown table."""
        pattern = rf'\|\s*\*\*{field_name}\*\*\s*\|\s*([^|]+)\s*\|'
        match = re.search(pattern, content)
        return match.group(1).strip() if match else default
    
    def _extract_description(self, content: str) -> str:
        """Extract the As a/I want/So that description (preserving markdown format)."""
        desc_pattern = r'\*\*As a\*\*\s*([^\n]+)\s*\n\s*\*\*I want\*\*\s*([^\n]+)\s*\n\s*\*\*So that\*\*\s*([^\n]+)'
        match = re.search(desc_pattern, content)
        if match:
            return f"**As a** {match.group(1).strip()}\n**I want** {match.group(2).strip()}\n**So that** {match.group(3).strip()}"
        return ""
    
    def _extract_acceptance_criteria(self, content: str) -> list[str]:
        """Extract acceptance criteria checkboxes."""
        criteria = []
        ac_section = re.search(r'#### Acceptance Criteria\n([\s\S]*?)(?=####|\n---|\Z)', content)
        if ac_section:
            for match in re.finditer(r'- \[[ x]\]\s*(.+)', ac_section.group(1)):
                criteria.append(match.group(1).strip())
        return criteria
    
    def _extract_subtasks(self, content: str) -> list[Subtask]:
        """Extract subtasks from the markdown table."""
        subtasks = []
        
        subtasks_section = re.search(r'#### Subtasks\n([\s\S]*?)(?=####|\n---|\Z)', content)
        if subtasks_section:
            # Parse table rows: | # | Subtask | Description | SP | Status |
            row_pattern = r'\|\s*(\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*(\d+)\s*\|\s*([^|]+)\s*\|'
            for match in re.finditer(row_pattern, subtasks_section.group(1)):
                subtasks.append(Subtask(
                    number=int(match.group(1)),
                    name=match.group(2).strip(),
                    description=match.group(3).strip(),
                    story_points=int(match.group(4)),
                    status=StoryStatus.from_string(match.group(5)),
                ))
        
        return subtasks
    
    def _extract_commits(self, content: str) -> list[Commit]:
        """Extract related commits from the markdown table."""
        commits = []
        
        commits_section = re.search(r'#### Related Commits\n([\s\S]*?)(?=####|\n---|\Z)', content)
        if commits_section:
            row_pattern = r'\|\s*`([^`]+)`\s*\|\s*([^|]+)\s*\|'
            for match in re.finditer(row_pattern, commits_section.group(1)):
                commits.append(Commit(
                    hash=match.group(1).strip(),
                    message=match.group(2).strip(),
                ))
        
        return commits
    
    def _extract_technical_notes(self, content: str) -> str:
        """Extract technical notes section."""
        notes_section = re.search(r'#### Technical Notes\n([\s\S]*?)(?=####|\Z)', content)
        if notes_section:
            return notes_section.group(1).strip()
        return ""


# =============================================================================
# Jira Client
# =============================================================================

class JiraClient:
    """Client for interacting with Jira REST API."""
    
    # Field IDs - these may vary by Jira instance
    STORY_POINTS_FIELD = "customfield_10014"  # Common default
    
    # Workflow transition IDs - these may vary by project
    TRANSITIONS = {
        "Analyze": {"to_open": "7"},
        "Open": {"to_in_progress": "4", "to_resolved": "5"},
        "In Progress": {"to_resolved": "5", "to_open": "301"},
    }
    
    def __init__(self, config: Config, dry_run: bool = True):
        self.config = config
        self.dry_run = dry_run
        self.base_url = f"{config.jira_url}/rest/api/3"
        self.auth = (config.jira_email, config.jira_api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.logger = logging.getLogger("JiraClient")
        self._current_user_account_id = None
    
    def get_current_user_account_id(self) -> str:
        """Get the account ID of the currently authenticated user."""
        if self._current_user_account_id is None:
            data = self._request("GET", "myself")
            self._current_user_account_id = data["accountId"]
        return self._current_user_account_id
        
    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an authenticated request to Jira API."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(
            method,
            url,
            auth=self.auth,
            headers=self.headers,
            **kwargs
        )
        
        if not response.ok:
            self.logger.error(f"Jira API error: {response.status_code} - {response.text}")
            response.raise_for_status()
        
        return response.json() if response.text else {}
    
    def _search_jql(self, jql: str, fields: list[str], max_results: int = 100) -> dict:
        """Use the JQL search API."""
        url = f"{self.base_url}/search/jql"
        payload = {
            "jql": jql,
            "maxResults": max_results,
            "fields": fields
        }
        response = requests.post(url, auth=self.auth, headers=self.headers, json=payload)
        
        if not response.ok:
            self.logger.error(f"Jira search error: {response.status_code} - {response.text}")
            response.raise_for_status()
        
        return response.json()
    
    def get_issue(self, issue_key: str) -> JiraIssue:
        """Fetch a single issue with its details."""
        data = self._request("GET", f"issue/{issue_key}", params={
            "fields": "summary,description,status,issuetype,subtasks"
        })
        
        subtasks = []
        if "subtasks" in data["fields"]:
            for st in data["fields"]["subtasks"]:
                subtasks.append(JiraIssue(
                    key=st["key"],
                    summary=st["fields"]["summary"],
                    description=None,
                    status=st["fields"]["status"]["name"],
                    issue_type="Sub-task",
                ))
        
        return JiraIssue(
            key=data["key"],
            summary=data["fields"]["summary"],
            description=data["fields"].get("description"),
            status=data["fields"]["status"]["name"],
            issue_type=data["fields"]["issuetype"]["name"],
            subtasks=subtasks,
        )
    
    def get_epic_children(self, epic_key: str) -> list[JiraIssue]:
        """Fetch all children (user stories) of an epic."""
        jql = f'parent = {epic_key} ORDER BY key ASC'
        
        data = self._search_jql(jql, ["summary", "description", "status", "issuetype", "subtasks"])
        
        children = []
        for issue in data.get("issues", []):
            subtasks = []
            for st in issue["fields"].get("subtasks", []):
                subtasks.append(JiraIssue(
                    key=st["key"],
                    summary=st["fields"]["summary"],
                    description=None,
                    status=st["fields"]["status"]["name"],
                    issue_type="Sub-task",
                ))
            
            children.append(JiraIssue(
                key=issue["key"],
                summary=issue["fields"]["summary"],
                description=issue["fields"].get("description"),
                status=issue["fields"]["status"]["name"],
                issue_type=issue["fields"]["issuetype"]["name"],
                subtasks=subtasks,
            ))
        
        return children
    
    def get_issue_comments(self, issue_key: str) -> list[dict]:
        """Fetch comments for an issue."""
        data = self._request("GET", f"issue/{issue_key}/comment")
        return data.get("comments", [])
    
    def update_issue_description(self, issue_key: str, description: str) -> bool:
        """Update an issue's description."""
        if self.dry_run:
            self.logger.info(f"[DRY-RUN] Would update description for {issue_key}")
            return True
        
        adf_description = self._text_to_adf(description)
        
        self._request("PUT", f"issue/{issue_key}", json={
            "fields": {
                "description": adf_description
            }
        })
        self.logger.info(f"Updated description for {issue_key}")
        return True
    
    def create_subtask(self, parent_key: str, summary: str, description: str, 
                       project_key: str, story_points: int = None) -> Optional[str]:
        """Create a subtask under a parent issue with assignee and story points."""
        if self.dry_run:
            self.logger.info(f"[DRY-RUN] Would create subtask '{summary[:50]}...' under {parent_key}")
            return None
        
        adf_description = self._text_to_adf(description)
        account_id = self.get_current_user_account_id()
        
        fields = {
            "project": {"key": project_key},
            "parent": {"key": parent_key},
            "summary": summary[:255],
            "description": adf_description,
            "issuetype": {"name": "Sub-task"},
            "assignee": {"accountId": account_id},
        }
        
        if story_points is not None:
            fields[self.STORY_POINTS_FIELD] = float(story_points)
        
        data = self._request("POST", "issue", json={"fields": fields})
        
        new_key = data.get("key")
        self.logger.info(f"Created subtask {new_key} under {parent_key}")
        return new_key
    
    def update_subtask(self, issue_key: str, description: str = None, 
                       story_points: int = None, assign_to_me: bool = False) -> bool:
        """Update an existing subtask's description, story points, and/or assignee."""
        if self.dry_run:
            self.logger.info(f"[DRY-RUN] Would update subtask {issue_key}")
            return True
        
        fields = {}
        
        if description is not None:
            fields["description"] = self._text_to_adf(description)
        
        if story_points is not None:
            fields[self.STORY_POINTS_FIELD] = float(story_points)
        
        if assign_to_me:
            fields["assignee"] = {"accountId": self.get_current_user_account_id()}
        
        if fields:
            self._request("PUT", f"issue/{issue_key}", json={"fields": fields})
            self.logger.info(f"Updated subtask {issue_key}")
        
        return True
    
    def get_subtask_details(self, issue_key: str) -> dict:
        """Get full details of a subtask."""
        data = self._request("GET", f"issue/{issue_key}", params={
            "fields": f"summary,description,assignee,status,{self.STORY_POINTS_FIELD}"
        })
        return {
            "key": data["key"],
            "summary": data["fields"]["summary"],
            "description": data["fields"].get("description"),
            "assignee": data["fields"].get("assignee"),
            "story_points": data["fields"].get(self.STORY_POINTS_FIELD),
            "status": data["fields"]["status"]["name"],
        }
    
    def get_issue_status(self, issue_key: str) -> str:
        """Get the current status of an issue."""
        data = self._request("GET", f"issue/{issue_key}", params={"fields": "status"})
        return data["fields"]["status"]["name"]
    
    def transition_issue(self, issue_key: str, transition_id: str, resolution: str = None) -> bool:
        """Transition an issue using a specific transition ID."""
        if self.dry_run:
            self.logger.info(f"[DRY-RUN] Would transition {issue_key} with transition {transition_id}")
            return True
        
        payload = {"transition": {"id": transition_id}}
        
        if resolution:
            payload["fields"] = {"resolution": {"name": resolution}}
        
        response = requests.post(
            f"{self.base_url}/issue/{issue_key}/transitions",
            auth=self.auth,
            headers=self.headers,
            json=payload
        )
        
        if response.ok or response.status_code == 204:
            self.logger.debug(f"Transitioned {issue_key} with transition {transition_id}")
            return True
        else:
            self.logger.error(f"Failed to transition {issue_key}: {response.text}")
            return False
    
    def transition_to_status(self, issue_key: str, target_status: str) -> bool:
        """Transition an issue to a target status, going through intermediate states if needed."""
        current_status = self.get_issue_status(issue_key)
        
        if current_status == target_status:
            return True
        
        if self.dry_run:
            self.logger.info(f"[DRY-RUN] Would transition {issue_key}: {current_status} → {target_status}")
            return True
        
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
            path = [
                ("Analyze", "7", None),
            ]
        else:
            self.logger.warning(f"Unknown target status: {target_status}")
            return False
        
        for from_status, transition_id, resolution in path:
            current_status = self.get_issue_status(issue_key)
            if current_status == from_status:
                if not self.transition_issue(issue_key, transition_id, resolution=resolution):
                    return False
        
        final_status = self.get_issue_status(issue_key)
        return target_lower in final_status.lower() or final_status == target_status
    
    def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add a comment to an issue."""
        if self.dry_run:
            self.logger.info(f"[DRY-RUN] Would add comment to {issue_key}")
            return True
        
        adf_comment = self._text_to_adf(comment)
        
        self._request("POST", f"issue/{issue_key}/comment", json={
            "body": adf_comment
        })
        self.logger.info(f"Added comment to {issue_key}")
        return True
    
    def add_commits_comment(self, issue_key: str, commits: list) -> bool:
        """Add a properly formatted commits table comment to an issue."""
        if self.dry_run:
            self.logger.info(f"[DRY-RUN] Would add commits comment to {issue_key} ({len(commits)} commits)")
            return True
        
        adf_comment = self._commits_to_adf(commits)
        
        self._request("POST", f"issue/{issue_key}/comment", json={
            "body": adf_comment
        })
        self.logger.info(f"Added commits comment to {issue_key}")
        return True
    
    def _commits_to_adf(self, commits: list) -> dict:
        """Convert commits list to proper Atlassian Document Format with table."""
        table_rows = []
        
        table_rows.append({
            "type": "tableRow",
            "content": [
                {
                    "type": "tableHeader",
                    "attrs": {},
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Commit", "marks": [{"type": "strong"}]}]}]
                },
                {
                    "type": "tableHeader",
                    "attrs": {},
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Message", "marks": [{"type": "strong"}]}]}]
                }
            ]
        })
        
        for commit in commits:
            table_rows.append({
                "type": "tableRow",
                "content": [
                    {
                        "type": "tableCell",
                        "attrs": {},
                        "content": [{"type": "paragraph", "content": [{"type": "text", "text": commit.hash, "marks": [{"type": "code"}]}]}]
                    },
                    {
                        "type": "tableCell",
                        "attrs": {},
                        "content": [{"type": "paragraph", "content": [{"type": "text", "text": commit.message}]}]
                    }
                ]
            })
        
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 3},
                    "content": [{"type": "text", "text": "Related Commits"}]
                },
                {
                    "type": "table",
                    "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
                    "content": table_rows
                }
            ]
        }
    
    def _text_to_adf(self, text: str) -> dict:
        """Convert plain text/markdown to Atlassian Document Format."""
        paragraphs = []
        current_list = None
        current_list_type = None
        
        for line in text.split("\n"):
            if not line.strip():
                current_list = None
                current_list_type = None
                continue
            
            if line.startswith("h2. "):
                current_list = None
                paragraphs.append({
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": line[4:]}]
                })
            elif line.startswith("h3. "):
                current_list = None
                paragraphs.append({
                    "type": "heading",
                    "attrs": {"level": 3},
                    "content": [{"type": "text", "text": line[4:]}]
                })
            elif line.startswith("## "):
                current_list = None
                paragraphs.append({
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": line[3:]}]
                })
            elif line.startswith("### "):
                current_list = None
                paragraphs.append({
                    "type": "heading",
                    "attrs": {"level": 3},
                    "content": [{"type": "text", "text": line[4:]}]
                })
            elif re.match(r'^- \[[ x]\] ', line):
                is_checked = line[3] == 'x'
                item_text = line[6:]
                
                if current_list_type != 'task':
                    current_list = {
                        "type": "taskList",
                        "attrs": {"localId": ""},
                        "content": []
                    }
                    current_list_type = 'task'
                    paragraphs.append(current_list)
                
                item_content = self._parse_inline_formatting(item_text)
                current_list["content"].append({
                    "type": "taskItem",
                    "attrs": {"localId": "", "state": "DONE" if is_checked else "TODO"},
                    "content": item_content
                })
            elif line.startswith("* "):
                item_text = line[2:]
                
                if current_list_type != 'bullet':
                    current_list = {
                        "type": "bulletList",
                        "content": []
                    }
                    current_list_type = 'bullet'
                    paragraphs.append(current_list)
                
                content = self._parse_inline_formatting(item_text)
                current_list["content"].append({
                    "type": "listItem",
                    "content": [{"type": "paragraph", "content": content}]
                })
            elif line.startswith("- ") and not line.startswith("- ["):
                item_text = line[2:]
                
                if current_list_type != 'bullet':
                    current_list = {
                        "type": "bulletList",
                        "content": []
                    }
                    current_list_type = 'bullet'
                    paragraphs.append(current_list)
                
                content = self._parse_inline_formatting(item_text)
                current_list["content"].append({
                    "type": "listItem",
                    "content": [{"type": "paragraph", "content": content}]
                })
            elif line.startswith("|"):
                current_list = None
                current_list_type = None
                continue
            else:
                current_list = None
                current_list_type = None
                content = self._parse_inline_formatting(line)
                paragraphs.append({
                    "type": "paragraph",
                    "content": content
                })
        
        return {
            "type": "doc",
            "version": 1,
            "content": paragraphs if paragraphs else [{"type": "paragraph", "content": [{"type": "text", "text": " "}]}]
        }
    
    def _parse_inline_formatting(self, text: str) -> list:
        """Parse inline formatting: **bold**, *italic*, `code`."""
        content = []
        pattern = r'(\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`)'
        last_end = 0
        
        for match in re.finditer(pattern, text):
            if match.start() > last_end:
                plain_text = text[last_end:match.start()]
                if plain_text:
                    content.append({"type": "text", "text": plain_text})
            
            full_match = match.group(0)
            
            if full_match.startswith("**"):
                content.append({
                    "type": "text",
                    "text": match.group(2),
                    "marks": [{"type": "strong"}]
                })
            elif full_match.startswith("`"):
                content.append({
                    "type": "text",
                    "text": match.group(4),
                    "marks": [{"type": "code"}]
                })
            elif full_match.startswith("*"):
                content.append({
                    "type": "text",
                    "text": match.group(3),
                    "marks": [{"type": "em"}]
                })
            
            last_end = match.end()
        
        if last_end < len(text):
            remaining = text[last_end:]
            if remaining:
                content.append({"type": "text", "text": remaining})
        
        return content if content else [{"type": "text", "text": text}]


# =============================================================================
# Sync Engine
# =============================================================================

class JiraSyncEngine:
    """Engine for synchronizing markdown stories with Jira."""
    
    def __init__(self, client: JiraClient, parser: MarkdownEpicParser, 
                 dry_run: bool = True, confirm: bool = True):
        self.client = client
        self.parser = parser
        self.dry_run = dry_run
        self.confirm = confirm
        self.logger = logging.getLogger("SyncEngine")
        
    def export_current_state(self, epic_key: str, output_path: Path):
        """Export current Jira state to JSON for backup."""
        self.logger.info(f"Exporting current state of epic {epic_key}...")
        
        epic = self.client.get_issue(epic_key)
        children = self.client.get_epic_children(epic_key)
        
        detailed_children = []
        for child in children:
            comments = self.client.get_issue_comments(child.key)
            
            detailed_children.append({
                "key": child.key,
                "summary": child.summary,
                "description": child.description,
                "status": child.status,
                "issue_type": child.issue_type,
                "subtasks": [{"key": st.key, "summary": st.summary, "status": st.status} for st in child.subtasks],
                "comments": comments,
            })
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "epic": {
                "key": epic.key,
                "summary": epic.summary,
                "description": epic.description,
                "status": epic.status,
            },
            "children": detailed_children,
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(export_data, indent=2, default=str))
        self.logger.info(f"Exported to {output_path}")
        return export_data
    
    def _match_stories(self, md_stories: list[UserStory], jira_stories: list[JiraIssue]) -> dict:
        """Match markdown stories to Jira issues by normalized title."""
        matches = {}
        
        jira_by_title = {}
        for jira in jira_stories:
            normalized = jira.normalize_title()
            jira_by_title[normalized] = jira
        
        for md in md_stories:
            normalized = md.normalize_title()
            
            if normalized in jira_by_title:
                matches[md.id] = (md, jira_by_title[normalized])
                continue
            
            for jira_title, jira in jira_by_title.items():
                if normalized in jira_title or jira_title in normalized:
                    matches[md.id] = (md, jira)
                    break
        
        return matches
    
    def analyze(self, epic_key: str) -> dict:
        """Analyze differences between markdown and Jira."""
        self.logger.info("Parsing markdown file...")
        md_stories = self.parser.parse()
        
        self.logger.info(f"Found {len(md_stories)} user stories in markdown")
        
        self.logger.info(f"Fetching Jira epic {epic_key}...")
        jira_children = self.client.get_epic_children(epic_key)
        
        self.logger.info(f"Found {len(jira_children)} children in Jira")
        
        matches = self._match_stories(md_stories, jira_children)
        
        analysis = {
            "stories_in_md": len(md_stories),
            "stories_in_jira": len(jira_children),
            "matched": [],
            "missing_in_jira": [],
            "missing_description": [],
            "missing_subtasks": [],
            "missing_commits_comment": [],
        }
        
        for story_id, (md_story, jira_story) in matches.items():
            analysis["matched"].append({
                "id": story_id,
                "jira_key": jira_story.key,
                "md_title": md_story.title,
                "jira_summary": jira_story.summary,
            })
            
            if not jira_story.has_description():
                analysis["missing_description"].append({
                    "id": story_id,
                    "jira_key": jira_story.key,
                })
            
            existing_subtasks_map = {st.summary.lower(): st for st in jira_story.subtasks}
            missing_subtasks = []
            
            for subtask in md_story.subtasks:
                subtask_name_lower = subtask.name.lower()
                matched = False
                for existing_name in existing_subtasks_map:
                    if subtask_name_lower[:30] in existing_name or existing_name in subtask_name_lower:
                        matched = True
                        break
                if not matched:
                    missing_subtasks.append(subtask)
            
            if missing_subtasks:
                analysis["missing_subtasks"].append({
                    "id": story_id,
                    "jira_key": jira_story.key,
                    "existing_count": len(jira_story.subtasks),
                    "missing_count": len(missing_subtasks),
                })
            
            if md_story.commits:
                comments = self.client.get_issue_comments(jira_story.key)
                has_commits_comment = any("Related Commits" in str(c.get("body", "")) for c in comments)
                if not has_commits_comment:
                    analysis["missing_commits_comment"].append({
                        "id": story_id,
                        "jira_key": jira_story.key,
                        "commits_count": len(md_story.commits),
                    })
        
        for md_story in md_stories:
            if md_story.id not in matches:
                analysis["missing_in_jira"].append({
                    "id": md_story.id,
                    "title": md_story.title,
                })
        
        return analysis
    
    def sync(self, epic_key: str, project_key: str = None, phase: int = None):
        """Perform the synchronization."""
        if project_key is None:
            project_key = epic_key.split("-")[0]
        
        analysis = self.analyze(epic_key)
        self._print_analysis(analysis)
        
        if self.dry_run:
            self.logger.info("\n" + "="*60)
            self.logger.info("DRY-RUN MODE - No changes will be made")
            self.logger.info("Run with --execute to apply changes")
            self.logger.info("="*60)
            return
        
        md_stories = {s.id: s for s in self.parser.parse()}
        jira_children = self.client.get_epic_children(epic_key)
        matches = self._match_stories(list(md_stories.values()), jira_children)
        
        run_phase = lambda p: phase is None or phase == p
        
        # Phase 1: Update missing descriptions
        if run_phase(1) and analysis["missing_description"]:
            self.logger.info("\n--- Phase 1: Updating Missing Descriptions ---")
            for item in analysis["missing_description"]:
                md_story = md_stories[item["id"]]
                if self._confirm_action(f"Update description for {item['jira_key']} ({item['id']})?"):
                    self.client.update_issue_description(
                        item["jira_key"],
                        md_story.to_jira_description()
                    )
        
        # Phase 2: Create missing subtasks
        if run_phase(2) and analysis["missing_subtasks"]:
            self.logger.info("\n--- Phase 2: Creating Missing Subtasks ---")
            for item in analysis["missing_subtasks"]:
                md_story = md_stories[item["id"]]
                jira_key = item["jira_key"]
                
                _, jira_story = matches[item["id"]]
                existing_summaries = {st.summary.lower() for st in jira_story.subtasks}
                
                for subtask in md_story.subtasks:
                    subtask_name_lower = subtask.name.lower()
                    if not any(subtask_name_lower[:30] in s or s in subtask_name_lower for s in existing_summaries):
                        if self._confirm_action(f"Create subtask '{subtask.name[:50]}...' under {jira_key}?"):
                            self.client.create_subtask(
                                jira_key,
                                subtask.name,
                                subtask.description,
                                project_key,
                                story_points=subtask.story_points,
                            )
        
        # Phase 3: Add commits comments
        if run_phase(3) and analysis["missing_commits_comment"]:
            self.logger.info("\n--- Phase 3: Adding Commits Comments ---")
            for item in analysis["missing_commits_comment"]:
                md_story = md_stories[item["id"]]
                if md_story.commits and self._confirm_action(f"Add commits comment to {item['jira_key']} ({item['commits_count']} commits)?"):
                    self.client.add_commits_comment(
                        item["jira_key"],
                        md_story.commits
                    )
        
        self.logger.info("\n✅ Sync complete!")
    
    def validate(self, epic_key: str):
        """Validate all user stories are correctly synced."""
        self.logger.info("Validating Jira sync...")
        
        md_stories = {s.id: s for s in self.parser.parse()}
        jira_children = self.client.get_epic_children(epic_key)
        matches = self._match_stories(list(md_stories.values()), jira_children)
        
        print("\n" + "="*70)
        print("VALIDATION REPORT")
        print("="*70)
        
        issues_found = 0
        
        for story_id, (md_story, jira_story) in matches.items():
            story_issues = []
            
            if not jira_story.has_description():
                story_issues.append("❌ Missing description")
            
            expected_subtasks = len(md_story.subtasks)
            actual_subtasks = len(jira_story.subtasks)
            if actual_subtasks < expected_subtasks:
                story_issues.append(f"❌ Missing subtasks ({actual_subtasks}/{expected_subtasks})")
            
            if md_story.commits:
                comments = self.client.get_issue_comments(jira_story.key)
                has_valid_commits = False
                has_broken_commits = False
                
                for c in comments:
                    body_str = json.dumps(c.get("body", {}))
                    if "Related Commits" in body_str:
                        if "tableCell" in body_str:
                            has_valid_commits = True
                        else:
                            has_broken_commits = True
                
                if has_broken_commits and not has_valid_commits:
                    story_issues.append("❌ Broken commits comment (no table)")
                elif not has_valid_commits:
                    story_issues.append("❌ Missing commits comment")
            
            if story_issues:
                issues_found += 1
                print(f"\n{jira_story.key} ({story_id}): {jira_story.summary[:40]}...")
                for issue in story_issues:
                    print(f"   {issue}")
        
        print("\n" + "="*70)
        if issues_found == 0:
            print("✅ All stories validated successfully!")
        else:
            print(f"⚠️  Found issues in {issues_found} stories")
        print("="*70)
    
    def fix_descriptions(self, epic_key: str, story_filter: str = None):
        """Re-sync all story descriptions with corrected formatting."""
        self.logger.info("Fixing story descriptions with corrected formatting...")
        
        md_stories = {s.id: s for s in self.parser.parse()}
        jira_children = self.client.get_epic_children(epic_key)
        matches = self._match_stories(list(md_stories.values()), jira_children)
        
        if story_filter:
            story_filter_upper = story_filter.upper()
            matches = {
                k: v for k, v in matches.items() 
                if story_filter_upper in k.upper() or story_filter_upper in v[1].key.upper()
            }
        
        total_updated = 0
        total_skipped = 0
        total_failed = 0
        
        print(f"\n{'='*70}")
        print("DESCRIPTION FIX")
        print(f"{'='*70}")
        
        for story_id, (md_story, jira_story) in matches.items():
            description = md_story.to_jira_description()
            
            if not description.strip():
                total_skipped += 1
                continue
            
            print(f"\n📝 {jira_story.key} ({story_id}): {md_story.title[:40]}...")
            
            if self.dry_run:
                self.logger.info(f"[DRY-RUN] Would update description for {jira_story.key}")
                total_updated += 1
            else:
                try:
                    self.client.update_issue_description(jira_story.key, description)
                    total_updated += 1
                    print(f"   ✅ Updated")
                except Exception as e:
                    total_failed += 1
                    print(f"   ❌ Failed: {e}")
        
        print(f"\n{'='*70}")
        print(f"SUMMARY:")
        print(f"   Updated: {total_updated}")
        print(f"   Skipped (no description): {total_skipped}")
        print(f"   Failed: {total_failed}")
        if self.dry_run:
            print(f"\n   (DRY-RUN mode - no changes made. Use --execute to apply.)")
        print(f"{'='*70}")
    
    def sync_subtask_statuses(self, epic_key: str, story_filter: str = None):
        """Sync subtask statuses from markdown to Jira."""
        self.logger.info("Syncing subtask statuses from markdown to Jira...")
        
        md_stories = {s.id: s for s in self.parser.parse()}
        jira_children = self.client.get_epic_children(epic_key)
        matches = self._match_stories(list(md_stories.values()), jira_children)
        
        if story_filter:
            story_filter_upper = story_filter.upper()
            matches = {
                k: v for k, v in matches.items() 
                if story_filter_upper in k.upper() or story_filter_upper in v[1].key.upper()
            }
        
        total_updated = 0
        total_skipped = 0
        total_failed = 0
        
        print(f"\n{'='*70}")
        print("SUBTASK STATUS SYNC")
        print(f"{'='*70}")
        
        for story_id, (md_story, jira_story) in matches.items():
            if not md_story.subtasks:
                continue
            
            print(f"\n📋 {jira_story.key} ({story_id}): {md_story.title[:40]}...")
            
            jira_subtasks_map = {}
            for jira_st in jira_story.subtasks:
                details = self.client.get_subtask_details(jira_st.key)
                jira_subtasks_map[jira_st.summary.lower()[:30]] = {
                    "key": jira_st.key,
                    "status": details["status"],
                    "summary": jira_st.summary,
                }
            
            for md_subtask in md_story.subtasks:
                md_name_lower = md_subtask.name.lower()[:30]
                matched_jira = None
                
                for jira_name, jira_data in jira_subtasks_map.items():
                    if md_name_lower in jira_name or jira_name in md_name_lower:
                        matched_jira = jira_data
                        break
                
                if not matched_jira:
                    continue
                
                md_status = md_subtask.status
                if md_status == StoryStatus.DONE:
                    target_status = "Resolved"
                elif md_status == StoryStatus.IN_PROGRESS:
                    target_status = "In Progress"
                else:
                    target_status = "Open"
                
                current_status = matched_jira["status"]
                
                if self._status_matches(current_status, target_status):
                    total_skipped += 1
                    continue
                
                print(f"   {matched_jira['key']}: {current_status} → {target_status}")
                
                if self.dry_run:
                    self.logger.info(f"[DRY-RUN] Would transition {matched_jira['key']}: {current_status} → {target_status}")
                    total_updated += 1
                else:
                    if self.client.transition_to_status(matched_jira['key'], target_status):
                        total_updated += 1
                    else:
                        total_failed += 1
                        print(f"      ❌ Failed to transition")
        
        print(f"\n{'='*70}")
        print(f"SUMMARY:")
        print(f"   Updated: {total_updated}")
        print(f"   Skipped (already correct): {total_skipped}")
        print(f"   Failed: {total_failed}")
        if self.dry_run:
            print(f"\n   (DRY-RUN mode - no changes made. Use --execute to apply.)")
        print(f"{'='*70}")
    
    def _status_matches(self, current: str, target: str) -> bool:
        """Check if current status matches target status."""
        current_lower = current.lower()
        target_lower = target.lower()
        
        if current_lower == target_lower:
            return True
        
        if target_lower in ["resolved", "done", "closed"]:
            return current_lower in ["resolved", "done", "closed"]
        
        if "progress" in target_lower:
            return "progress" in current_lower
        
        if target_lower == "open":
            return current_lower == "open"
        
        return False
    
    def _print_analysis(self, analysis: dict):
        """Print analysis results."""
        print("\n" + "="*60)
        print("ANALYSIS RESULTS")
        print("="*60)
        
        print(f"\n📊 Summary:")
        print(f"   Stories in markdown: {analysis['stories_in_md']}")
        print(f"   Stories in Jira: {analysis['stories_in_jira']}")
        print(f"   Matched: {len(analysis['matched'])}")
        
        if analysis["missing_in_jira"]:
            print(f"\n⚠️  Stories in markdown but NOT matched in Jira ({len(analysis['missing_in_jira'])}):")
            for item in analysis["missing_in_jira"][:10]:
                print(f"   - {item['id']}: {item['title'][:50]}")
            if len(analysis["missing_in_jira"]) > 10:
                print(f"   ... and {len(analysis['missing_in_jira']) - 10} more")
        
        if analysis["missing_description"]:
            print(f"\n📝 Stories missing description ({len(analysis['missing_description'])}):")
            for item in analysis["missing_description"][:10]:
                print(f"   - {item['jira_key']} ({item['id']})")
            if len(analysis["missing_description"]) > 10:
                print(f"   ... and {len(analysis['missing_description']) - 10} more")
        
        if analysis["missing_subtasks"]:
            print(f"\n📋 Stories missing subtasks ({len(analysis['missing_subtasks'])}):")
            for item in analysis["missing_subtasks"][:10]:
                print(f"   - {item['jira_key']} ({item['id']}): {item['missing_count']} missing subtasks")
            if len(analysis["missing_subtasks"]) > 10:
                print(f"   ... and {len(analysis['missing_subtasks']) - 10} more")
        
        if analysis["missing_commits_comment"]:
            print(f"\n💬 Stories missing commits comment ({len(analysis['missing_commits_comment'])}):")
            for item in analysis["missing_commits_comment"][:10]:
                print(f"   - {item['jira_key']} ({item['id']}): {item['commits_count']} commits")
            if len(analysis["missing_commits_comment"]) > 10:
                print(f"   ... and {len(analysis['missing_commits_comment']) - 10} more")
        
        print("\n" + "="*60)
    
    def _confirm_action(self, message: str) -> bool:
        """Ask for confirmation before an action."""
        if not self.confirm:
            return True
        
        response = input(f"\n{message} [y/N]: ").strip().lower()
        return response in ("y", "yes")


# =============================================================================
# Main
# =============================================================================

def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Sync markdown documentation with Jira",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--markdown", "-m",
        type=str,
        help="Path to the markdown file containing user stories"
    )
    
    parser.add_argument(
        "--epic", "-e",
        type=str,
        required=True,
        help="Jira epic key (e.g., PROJ-123)"
    )
    
    parser.add_argument(
        "--project", "-p",
        type=str,
        help="Jira project key for creating issues (defaults to epic prefix)"
    )
    
    parser.add_argument(
        "--jira-url",
        type=str,
        help="Jira instance URL (or set JIRA_URL env var)"
    )
    
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export current Jira state to JSON (safe, read-only)"
    )
    
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute changes (default is dry-run)"
    )
    
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompts (use with caution!)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only analyze differences, don't sync"
    )
    
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3],
        help="Run only a specific phase: 1=descriptions, 2=subtasks, 3=comments"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate all user stories are correctly synced"
    )
    
    parser.add_argument(
        "--fix-descriptions",
        action="store_true",
        help="Re-sync all story descriptions with corrected formatting"
    )
    
    parser.add_argument(
        "--sync-status",
        action="store_true",
        help="Sync subtask statuses from markdown to Jira"
    )
    
    parser.add_argument(
        "--story",
        type=str,
        help="Only process a specific story (e.g., US-001 or PROJ-123)"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger("main")
    
    # Determine if we need markdown file
    require_markdown = not args.export
    
    # Load and validate config
    config = Config(markdown_path=args.markdown, jira_url=args.jira_url)
    try:
        config.validate(require_markdown=require_markdown)
    except (ValueError, FileNotFoundError) as e:
        logger.error(str(e))
        return 1
    
    # Initialize components
    dry_run = not args.execute
    client = JiraClient(config, dry_run=dry_run)
    
    # For export, we don't need the markdown parser
    if args.export:
        engine = JiraSyncEngine(client, None, dry_run=dry_run, confirm=not args.no_confirm)
        output_dir = Path(__file__).parent / "exports"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"jira_export_{args.epic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        engine.export_current_state(args.epic, output_path)
        return 0
    
    # For other operations, we need the markdown file
    if not config.markdown_path:
        logger.error("Markdown file is required. Use --markdown or -m to specify.")
        return 1
    
    md_parser = MarkdownEpicParser(config.markdown_path)
    engine = JiraSyncEngine(client, md_parser, dry_run=dry_run, confirm=not args.no_confirm)
    
    # Handle analyze-only
    if args.analyze_only:
        analysis = engine.analyze(args.epic)
        engine._print_analysis(analysis)
        return 0
    
    # Handle validate
    if args.validate:
        engine.validate(args.epic)
        return 0
    
    # Handle fix-descriptions
    if args.fix_descriptions:
        if not args.execute:
            logger.info("Running fix-descriptions in DRY-RUN mode. Use --execute to actually fix.")
        engine.fix_descriptions(args.epic, story_filter=args.story)
        return 0
    
    # Handle sync-status
    if args.sync_status:
        if not args.execute:
            logger.info("Running sync-status in DRY-RUN mode. Use --execute to actually sync.")
        engine.sync_subtask_statuses(args.epic, story_filter=args.story)
        return 0
    
    # Run full sync
    if not dry_run:
        logger.warning("="*60)
        logger.warning("⚠️  EXECUTE MODE - Changes will be made to Jira!")
        logger.warning("="*60)
        if not args.no_confirm:
            response = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
            if response not in ("y", "yes"):
                logger.info("Aborted.")
                return 0
    
    project_key = args.project or args.epic.split("-")[0]
    engine.sync(args.epic, project_key, phase=args.phase)
    return 0


if __name__ == "__main__":
    exit(main())
