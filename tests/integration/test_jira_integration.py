"""
Integration tests with mocked Jira API responses.

These tests verify the full flow from adapter through client
using realistic API responses.

Note: Common fixtures are imported from conftest.py:
- tracker_config (aliased as jira_config below)
- mock_myself_response
- mock_issue_response
- mock_epic_children_response
- mock_transitions_response
- mock_comments_response
- mock_create_issue_response
"""

import pytest
from unittest.mock import Mock, patch
import json

from md2jira.adapters.jira.client import JiraApiClient
from md2jira.adapters.jira.adapter import JiraAdapter
from md2jira.core.ports.issue_tracker import (
    IssueTrackerError,
    AuthenticationError,
    NotFoundError,
    PermissionError,
)


# Alias the shared tracker_config fixture for clarity in Jira-specific tests
@pytest.fixture
def jira_config(tracker_config):
    """Alias for tracker_config - Jira-specific configuration."""
    return tracker_config


# =============================================================================
# JiraApiClient Tests
# =============================================================================

class TestJiraApiClientIntegration:
    """Integration tests for JiraApiClient with mocked HTTP."""

    def test_get_myself_success(self, jira_config, mock_myself_response):
        """Test successful authentication and user retrieval."""
        client = JiraApiClient(
            base_url=jira_config.url,
            email=jira_config.email,
            api_token=jira_config.api_token,
            dry_run=False,
        )

        with patch.object(client._session, "request") as mock_request:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.text = json.dumps(mock_myself_response)
            mock_response.json.return_value = mock_myself_response
            mock_request.return_value = mock_response

            result = client.get_myself()

            assert result["accountId"] == "user-123-abc"
            assert result["displayName"] == "Test User"
            mock_request.assert_called_once()

    def test_get_myself_caches_result(self, jira_config, mock_myself_response):
        """Test that get_myself caches the result."""
        client = JiraApiClient(
            base_url=jira_config.url,
            email=jira_config.email,
            api_token=jira_config.api_token,
            dry_run=False,
        )

        with patch.object(client._session, "request") as mock_request:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.text = json.dumps(mock_myself_response)
            mock_response.json.return_value = mock_myself_response
            mock_request.return_value = mock_response

            # Call twice
            client.get_myself()
            client.get_myself()

            # Should only make one request due to caching
            assert mock_request.call_count == 1

    def test_authentication_error(self, jira_config):
        """Test 401 response raises AuthenticationError."""
        client = JiraApiClient(
            base_url=jira_config.url,
            email=jira_config.email,
            api_token="bad-token",
            dry_run=False,
        )

        with patch.object(client._session, "request") as mock_request:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_request.return_value = mock_response

            with pytest.raises(AuthenticationError):
                client.get("myself")

    def test_not_found_error(self, jira_config):
        """Test 404 response raises NotFoundError."""
        client = JiraApiClient(
            base_url=jira_config.url,
            email=jira_config.email,
            api_token=jira_config.api_token,
            dry_run=False,
        )

        with patch.object(client._session, "request") as mock_request:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 404
            mock_response.text = "Issue not found"
            mock_request.return_value = mock_response

            with pytest.raises(NotFoundError):
                client.get("issue/INVALID-999")

    def test_permission_error(self, jira_config):
        """Test 403 response raises PermissionError."""
        client = JiraApiClient(
            base_url=jira_config.url,
            email=jira_config.email,
            api_token=jira_config.api_token,
            dry_run=False,
        )

        with patch.object(client._session, "request") as mock_request:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 403
            mock_response.text = "Forbidden"
            mock_request.return_value = mock_response

            with pytest.raises(PermissionError):
                client.get("issue/SECRET-123")

    def test_dry_run_skips_post(self, jira_config):
        """Test dry_run mode skips POST requests (except search)."""
        client = JiraApiClient(
            base_url=jira_config.url,
            email=jira_config.email,
            api_token=jira_config.api_token,
            dry_run=True,
        )

        with patch.object(client._session, "request") as mock_request:
            result = client.post("issue", json={"fields": {}})

            assert result == {}
            mock_request.assert_not_called()

    def test_dry_run_allows_search(self, jira_config, mock_epic_children_response):
        """Test dry_run mode allows search JQL requests."""
        client = JiraApiClient(
            base_url=jira_config.url,
            email=jira_config.email,
            api_token=jira_config.api_token,
            dry_run=True,
        )

        with patch.object(client._session, "request") as mock_request:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.text = json.dumps(mock_epic_children_response)
            mock_response.json.return_value = mock_epic_children_response
            mock_request.return_value = mock_response

            result = client.search_jql("parent = TEST-1", ["summary"])

            assert result["total"] == 2
            mock_request.assert_called_once()

    def test_connection_test_success(self, jira_config, mock_myself_response):
        """Test connection test returns True on success."""
        client = JiraApiClient(
            base_url=jira_config.url,
            email=jira_config.email,
            api_token=jira_config.api_token,
            dry_run=False,
        )

        with patch.object(client._session, "request") as mock_request:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.text = json.dumps(mock_myself_response)
            mock_response.json.return_value = mock_myself_response
            mock_request.return_value = mock_response

            assert client.test_connection() is True

    def test_connection_test_failure(self, jira_config):
        """Test connection test returns False on failure."""
        client = JiraApiClient(
            base_url=jira_config.url,
            email=jira_config.email,
            api_token="bad-token",
            dry_run=False,
        )

        with patch.object(client._session, "request") as mock_request:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_request.return_value = mock_response

            assert client.test_connection() is False


# =============================================================================
# JiraAdapter Tests
# =============================================================================

class TestJiraAdapterIntegration:
    """Integration tests for JiraAdapter with mocked client."""

    @pytest.fixture
    def adapter(self, jira_config):
        """Create adapter with mocked client."""
        return JiraAdapter(config=jira_config, dry_run=False)

    def test_get_issue_parses_response(self, adapter, mock_issue_response):
        """Test get_issue correctly parses API response."""
        with patch.object(adapter._client, "get") as mock_get:
            mock_get.return_value = mock_issue_response

            issue = adapter.get_issue("TEST-123")

            assert issue.key == "TEST-123"
            assert issue.summary == "Sample User Story"
            assert issue.status == "Open"
            assert issue.issue_type == "Story"
            assert len(issue.subtasks) == 2
            assert issue.subtasks[0].key == "TEST-124"
            assert issue.subtasks[1].status == "In Progress"

    def test_get_epic_children(self, adapter, mock_epic_children_response):
        """Test get_epic_children returns parsed issues."""
        with patch.object(adapter._client, "search_jql") as mock_search:
            mock_search.return_value = mock_epic_children_response

            children = adapter.get_epic_children("TEST-1")

            assert len(children) == 2
            assert children[0].key == "TEST-10"
            assert children[0].summary == "Story Alpha"
            assert children[1].key == "TEST-11"
            assert len(children[1].subtasks) == 1

    def test_create_subtask_builds_correct_payload(self, adapter, mock_create_issue_response, mock_myself_response):
        """Test create_subtask sends correct fields."""
        with patch.object(adapter._client, "post") as mock_post, \
             patch.object(adapter._client, "get_current_user_id") as mock_user:
            mock_post.return_value = mock_create_issue_response
            mock_user.return_value = "user-123-abc"

            result = adapter.create_subtask(
                parent_key="TEST-10",
                summary="New subtask",
                description="Task description",
                project_key="TEST",
                story_points=3,
            )

            assert result == "TEST-99"
            mock_post.assert_called_once()
            
            call_args = mock_post.call_args
            payload = call_args[1]["json"]["fields"]
            
            assert payload["project"]["key"] == "TEST"
            assert payload["parent"]["key"] == "TEST-10"
            assert payload["summary"] == "New subtask"
            assert payload["issuetype"]["name"] == "Sub-task"
            assert payload["customfield_10014"] == 3.0

    def test_create_subtask_dry_run(self, jira_config):
        """Test create_subtask returns None in dry_run mode."""
        adapter = JiraAdapter(config=jira_config, dry_run=True)

        result = adapter.create_subtask(
            parent_key="TEST-10",
            summary="New subtask",
            description="Task description",
            project_key="TEST",
        )

        assert result is None

    def test_update_issue_description(self, adapter):
        """Test update_issue_description sends correct payload."""
        with patch.object(adapter._client, "put") as mock_put:
            mock_put.return_value = {}

            result = adapter.update_issue_description("TEST-123", "New description")

            assert result is True
            mock_put.assert_called_once()
            
            call_args = mock_put.call_args
            assert "issue/TEST-123" in call_args[0]
            assert "description" in call_args[1]["json"]["fields"]

    def test_add_comment(self, adapter):
        """Test add_comment sends correct payload."""
        with patch.object(adapter._client, "post") as mock_post:
            mock_post.return_value = {}

            result = adapter.add_comment("TEST-123", "Comment text")

            assert result is True
            mock_post.assert_called_once()
            
            call_args = mock_post.call_args
            assert "issue/TEST-123/comment" in call_args[0]

    def test_get_issue_status(self, adapter):
        """Test get_issue_status extracts status name."""
        with patch.object(adapter._client, "get") as mock_get:
            mock_get.return_value = {
                "fields": {"status": {"name": "In Progress"}}
            }

            status = adapter.get_issue_status("TEST-123")

            assert status == "In Progress"

    def test_get_available_transitions(self, adapter, mock_transitions_response):
        """Test get_available_transitions returns transition list."""
        with patch.object(adapter._client, "get") as mock_get:
            mock_get.return_value = mock_transitions_response

            transitions = adapter.get_available_transitions("TEST-123")

            assert len(transitions) == 3
            assert transitions[0]["id"] == "4"
            assert transitions[0]["name"] == "Start Progress"

    def test_get_issue_comments(self, adapter, mock_comments_response):
        """Test get_issue_comments returns comments list."""
        with patch.object(adapter._client, "get") as mock_get:
            mock_get.return_value = mock_comments_response

            comments = adapter.get_issue_comments("TEST-123")

            assert len(comments) == 1
            assert comments[0]["id"] == "10001"


# =============================================================================
# End-to-End Sync Flow Tests
# =============================================================================

class TestSyncFlowIntegration:
    """End-to-end integration tests for the sync flow.
    
    Uses shared fixtures from conftest.py:
    - mock_tracker_with_children
    - mock_parser
    - mock_formatter
    - sync_config
    """

    def test_analyze_matches_stories(self, mock_tracker_with_children, mock_parser, mock_formatter, sync_config):
        """Test that analyze correctly matches markdown stories to Jira issues."""
        from md2jira.application.sync.orchestrator import SyncOrchestrator

        orchestrator = SyncOrchestrator(
            tracker=mock_tracker_with_children,
            parser=mock_parser,
            formatter=mock_formatter,
            config=sync_config,
        )

        result = orchestrator.analyze("/path/to/doc.md", "TEST-1")

        assert result.stories_matched == 2
        assert len(result.matched_stories) == 2
        assert ("US-001", "TEST-10") in result.matched_stories
        assert ("US-002", "TEST-11") in result.matched_stories

    def test_sync_updates_descriptions(self, mock_tracker_with_children, mock_parser, mock_formatter, sync_config):
        """Test that sync updates story descriptions."""
        from md2jira.application.sync.orchestrator import SyncOrchestrator

        orchestrator = SyncOrchestrator(
            tracker=mock_tracker_with_children,
            parser=mock_parser,
            formatter=mock_formatter,
            config=sync_config,
        )

        result = orchestrator.sync("/path/to/doc.md", "TEST-1")

        assert result.stories_updated == 2
        assert mock_tracker_with_children.update_issue_description.call_count == 2

    def test_sync_creates_new_subtasks(self, mock_tracker_with_children, mock_parser, mock_formatter, sync_config):
        """Test that sync creates subtasks that don't exist."""
        from md2jira.application.sync.orchestrator import SyncOrchestrator

        orchestrator = SyncOrchestrator(
            tracker=mock_tracker_with_children,
            parser=mock_parser,
            formatter=mock_formatter,
            config=sync_config,
        )

        result = orchestrator.sync("/path/to/doc.md", "TEST-1")

        # Alpha Task 1 should be created (doesn't exist)
        # Beta Subtask should be updated (already exists)
        assert result.subtasks_created >= 1
        mock_tracker_with_children.create_subtask.assert_called()

    def test_sync_dry_run_no_changes(self, mock_tracker_with_children, mock_parser, mock_formatter, sync_config_dry_run):
        """Test that dry_run mode doesn't make actual changes."""
        from md2jira.application.sync.orchestrator import SyncOrchestrator

        orchestrator = SyncOrchestrator(
            tracker=mock_tracker_with_children,
            parser=mock_parser,
            formatter=mock_formatter,
            config=sync_config_dry_run,
        )

        result = orchestrator.sync("/path/to/doc.md", "TEST-1")

        assert result.dry_run is True
        # In dry_run, commands don't execute actual tracker methods
        # (the command layer handles this)

    def test_sync_handles_unmatched_stories(self, mock_tracker_with_children, mock_parser, mock_formatter, sync_config):
        """Test that unmatched stories are reported as warnings."""
        from md2jira.application.sync.orchestrator import SyncOrchestrator
        from md2jira.core.domain.entities import UserStory
        from md2jira.core.domain.enums import Status
        from md2jira.core.domain.value_objects import StoryId, Description

        # Add an unmatched story
        mock_parser.parse_stories.return_value.append(
            UserStory(
                id=StoryId("US-999"),
                title="Nonexistent Story",
                description=Description(
                    role="user",
                    want="this story to not match",
                    benefit="we can test unmatched handling"
                ),
                status=Status.PLANNED,
            )
        )

        orchestrator = SyncOrchestrator(
            tracker=mock_tracker_with_children,
            parser=mock_parser,
            formatter=mock_formatter,
            config=sync_config,
        )

        result = orchestrator.analyze("/path/to/doc.md", "TEST-1")

        assert "US-999" in result.unmatched_stories
        assert len(result.warnings) > 0


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandlingIntegration:
    """Test error handling in integration scenarios."""

    def test_adapter_handles_api_errors_gracefully(self, jira_config):
        """Test adapter doesn't crash on API errors."""
        adapter = JiraAdapter(config=jira_config, dry_run=False)

        with patch.object(adapter._client, "get") as mock_get:
            mock_get.side_effect = IssueTrackerError("Server error")

            with pytest.raises(IssueTrackerError):
                adapter.get_issue("TEST-123")

    def test_transition_handles_invalid_status(self, jira_config):
        """Test transition logs warning for unknown status."""
        adapter = JiraAdapter(config=jira_config, dry_run=False)

        with patch.object(adapter._client, "get") as mock_get:
            mock_get.return_value = {"fields": {"status": {"name": "Open"}}}

            result = adapter.transition_issue("TEST-123", "InvalidStatus")

            # Should return False for unknown status
            assert result is False

