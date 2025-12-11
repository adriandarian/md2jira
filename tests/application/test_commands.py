"""Tests for application commands."""

import pytest
from unittest.mock import Mock, MagicMock

from md2jira.application.commands import (
    Command,
    CommandResult,
    CommandBatch,
    UpdateDescriptionCommand,
    CreateSubtaskCommand,
    AddCommentCommand,
    TransitionStatusCommand,
)
from md2jira.core.ports.issue_tracker import IssueData


class TestCommandResult:
    """Tests for CommandResult."""
    
    def test_ok(self):
        result = CommandResult.ok("data")
        assert result.success
        assert result.data == "data"
        assert not result.dry_run
    
    def test_ok_dry_run(self):
        result = CommandResult.ok("data", dry_run=True)
        assert result.success
        assert result.dry_run
    
    def test_fail(self):
        result = CommandResult.fail("error message")
        assert not result.success
        assert result.error == "error message"
    
    def test_skip(self):
        result = CommandResult.skip("reason")
        assert result.success
        assert result.skipped


class TestUpdateDescriptionCommand:
    """Tests for UpdateDescriptionCommand."""
    
    @pytest.fixture
    def mock_tracker(self):
        tracker = Mock()
        tracker.get_issue.return_value = IssueData(
            key="PROJ-123",
            summary="Test",
            description="Old description"
        )
        tracker.update_issue_description.return_value = True
        return tracker
    
    def test_validate_missing_key(self, mock_tracker):
        cmd = UpdateDescriptionCommand(
            tracker=mock_tracker,
            issue_key="",
            description="New description"
        )
        assert cmd.validate() is not None
    
    def test_validate_missing_description(self, mock_tracker):
        cmd = UpdateDescriptionCommand(
            tracker=mock_tracker,
            issue_key="PROJ-123",
            description=""
        )
        assert cmd.validate() is not None
    
    def test_execute_dry_run(self, mock_tracker):
        cmd = UpdateDescriptionCommand(
            tracker=mock_tracker,
            issue_key="PROJ-123",
            description="New description",
            dry_run=True
        )
        
        result = cmd.execute()
        
        assert result.success
        assert result.dry_run
        mock_tracker.update_issue_description.assert_not_called()
    
    def test_execute_success(self, mock_tracker):
        cmd = UpdateDescriptionCommand(
            tracker=mock_tracker,
            issue_key="PROJ-123",
            description="New description",
            dry_run=False
        )
        
        result = cmd.execute()
        
        assert result.success
        mock_tracker.update_issue_description.assert_called_once()


class TestCreateSubtaskCommand:
    """Tests for CreateSubtaskCommand."""
    
    @pytest.fixture
    def mock_tracker(self):
        tracker = Mock()
        tracker.create_subtask.return_value = "PROJ-456"
        return tracker
    
    def test_validate_missing_parent(self, mock_tracker):
        cmd = CreateSubtaskCommand(
            tracker=mock_tracker,
            parent_key="",
            project_key="PROJ",
            summary="Subtask"
        )
        assert cmd.validate() is not None
    
    def test_execute_dry_run(self, mock_tracker):
        cmd = CreateSubtaskCommand(
            tracker=mock_tracker,
            parent_key="PROJ-123",
            project_key="PROJ",
            summary="New subtask",
            dry_run=True
        )
        
        result = cmd.execute()
        
        assert result.success
        assert result.dry_run
        mock_tracker.create_subtask.assert_not_called()
    
    def test_execute_success(self, mock_tracker):
        cmd = CreateSubtaskCommand(
            tracker=mock_tracker,
            parent_key="PROJ-123",
            project_key="PROJ",
            summary="New subtask",
            dry_run=False
        )
        
        result = cmd.execute()
        
        assert result.success
        assert result.data == "PROJ-456"


class TestTransitionStatusCommand:
    """Tests for TransitionStatusCommand."""
    
    @pytest.fixture
    def mock_tracker(self):
        tracker = Mock()
        tracker.get_issue_status.return_value = "Open"
        tracker.transition_issue.return_value = True
        return tracker
    
    def test_execute_dry_run(self, mock_tracker):
        cmd = TransitionStatusCommand(
            tracker=mock_tracker,
            issue_key="PROJ-123",
            target_status="Resolved",
            dry_run=True
        )
        
        result = cmd.execute()
        
        assert result.success
        assert result.dry_run
    
    def test_execute_success(self, mock_tracker):
        cmd = TransitionStatusCommand(
            tracker=mock_tracker,
            issue_key="PROJ-123",
            target_status="Resolved",
            dry_run=False
        )
        
        result = cmd.execute()
        
        assert result.success
        mock_tracker.transition_issue.assert_called_with("PROJ-123", "Resolved")


class TestCommandBatch:
    """Tests for CommandBatch."""
    
    def test_execute_all_success(self):
        cmd1 = Mock()
        cmd1.execute.return_value = CommandResult.ok("result1")
        
        cmd2 = Mock()
        cmd2.execute.return_value = CommandResult.ok("result2")
        
        batch = CommandBatch()
        batch.add(cmd1).add(cmd2)
        
        results = batch.execute_all()
        
        assert len(results) == 2
        assert batch.all_succeeded
        assert batch.executed_count == 2
    
    def test_execute_stop_on_error(self):
        cmd1 = Mock()
        cmd1.execute.return_value = CommandResult.fail("error")
        
        cmd2 = Mock()
        cmd2.execute.return_value = CommandResult.ok()
        
        batch = CommandBatch(stop_on_error=True)
        batch.add(cmd1).add(cmd2)
        
        results = batch.execute_all()
        
        # Should stop after first failure
        assert len(results) == 1
        assert batch.failed_count == 1
        cmd2.execute.assert_not_called()
    
    def test_execute_continue_on_error(self):
        cmd1 = Mock()
        cmd1.execute.return_value = CommandResult.fail("error")
        
        cmd2 = Mock()
        cmd2.execute.return_value = CommandResult.ok()
        
        batch = CommandBatch(stop_on_error=False)
        batch.add(cmd1).add(cmd2)
        
        results = batch.execute_all()
        
        # Should continue despite failure
        assert len(results) == 2
        assert batch.failed_count == 1
        assert batch.executed_count == 1

