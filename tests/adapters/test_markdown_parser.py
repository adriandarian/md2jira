"""Tests for Markdown parser adapter."""

import pytest
from pathlib import Path
from textwrap import dedent

from md2jira.adapters.parsers import MarkdownParser


class TestMarkdownParser:
    """Tests for MarkdownParser."""
    
    @pytest.fixture
    def parser(self):
        return MarkdownParser()
    
    @pytest.fixture
    def sample_markdown(self):
        return dedent("""
        # Epic Title
        
        ## User Stories
        
        ### ✅ US-001: First Story
        
        | Field | Value |
        |-------|-------|
        | **Story Points** | 5 |
        | **Priority** | 🟡 High |
        | **Status** | ✅ Done |
        
        #### Description
        
        **As a** developer
        **I want** to test parsing
        **So that** the parser works correctly
        
        #### Acceptance Criteria
        
        - [x] Parser extracts story ID
        - [ ] Parser extracts title
        
        #### Subtasks
        
        | # | Subtask | Description | SP | Status |
        |---|---------|-------------|----|---------| 
        | 1 | Create parser | Build markdown parser | 3 | ✅ Done |
        | 2 | Add tests | Write unit tests | 2 | ✅ Done |
        
        #### Related Commits
        
        | Commit | Message |
        |--------|---------|
        | `abc1234` | Initial parser implementation |
        | `def5678` | Add test coverage |
        
        ---
        
        ### 🔄 US-002: Second Story
        
        | Field | Value |
        |-------|-------|
        | **Story Points** | 3 |
        | **Priority** | 🟢 Medium |
        | **Status** | 🔄 In Progress |
        
        #### Description
        
        **As a** user
        **I want** another feature
        **So that** I can do more
        """)
    
    def test_can_parse_markdown_file(self, parser, tmp_path):
        """Test parser recognizes markdown files."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")
        
        assert parser.can_parse(md_file)
    
    def test_can_parse_markdown_content(self, parser, sample_markdown):
        """Test parser recognizes markdown content."""
        assert parser.can_parse(sample_markdown)
    
    def test_supported_extensions(self, parser):
        """Test supported file extensions."""
        assert ".md" in parser.supported_extensions
        assert ".markdown" in parser.supported_extensions
    
    def test_parse_stories_count(self, parser, sample_markdown):
        """Test correct number of stories parsed."""
        stories = parser.parse_stories(sample_markdown)
        assert len(stories) == 2
    
    def test_parse_story_id(self, parser, sample_markdown):
        """Test story ID extraction."""
        stories = parser.parse_stories(sample_markdown)
        assert str(stories[0].id) == "US-001"
        assert str(stories[1].id) == "US-002"
    
    def test_parse_story_title(self, parser, sample_markdown):
        """Test story title extraction."""
        stories = parser.parse_stories(sample_markdown)
        assert stories[0].title == "First Story"
    
    def test_parse_story_points(self, parser, sample_markdown):
        """Test story points extraction."""
        stories = parser.parse_stories(sample_markdown)
        assert stories[0].story_points == 5
        assert stories[1].story_points == 3
    
    def test_parse_priority(self, parser, sample_markdown):
        """Test priority extraction."""
        from md2jira.core.domain import Priority
        
        stories = parser.parse_stories(sample_markdown)
        assert stories[0].priority == Priority.HIGH
        assert stories[1].priority == Priority.MEDIUM
    
    def test_parse_status(self, parser, sample_markdown):
        """Test status extraction."""
        from md2jira.core.domain import Status
        
        stories = parser.parse_stories(sample_markdown)
        assert stories[0].status == Status.DONE
        assert stories[1].status == Status.IN_PROGRESS
    
    def test_parse_description(self, parser, sample_markdown):
        """Test description extraction."""
        stories = parser.parse_stories(sample_markdown)
        desc = stories[0].description
        
        assert desc is not None
        assert desc.role == "developer"
        assert "test parsing" in desc.want
    
    def test_parse_acceptance_criteria(self, parser, sample_markdown):
        """Test acceptance criteria extraction."""
        stories = parser.parse_stories(sample_markdown)
        ac = stories[0].acceptance_criteria
        
        assert len(ac) == 2
        # First item is checked
        items = list(ac)
        assert items[0][1] is True  # checked
        assert items[1][1] is False  # not checked
    
    def test_parse_subtasks(self, parser, sample_markdown):
        """Test subtask extraction."""
        stories = parser.parse_stories(sample_markdown)
        subtasks = stories[0].subtasks
        
        assert len(subtasks) == 2
        assert subtasks[0].name == "Create parser"
        assert subtasks[0].story_points == 3
    
    def test_parse_commits(self, parser, sample_markdown):
        """Test commit extraction."""
        stories = parser.parse_stories(sample_markdown)
        commits = stories[0].commits
        
        assert len(commits) == 2
        assert commits[0].hash == "abc1234"
        assert "Initial parser" in commits[0].message
    
    def test_validate_valid_markdown(self, parser, sample_markdown):
        """Test validation of valid markdown."""
        errors = parser.validate(sample_markdown)
        assert len(errors) == 0
    
    def test_validate_missing_stories(self, parser):
        """Test validation catches missing stories."""
        content = "# Epic without stories"
        errors = parser.validate(content)
        assert len(errors) > 0
    
    def test_parse_from_file(self, parser, sample_markdown, tmp_path):
        """Test parsing from file path."""
        md_file = tmp_path / "epic.md"
        md_file.write_text(sample_markdown)
        
        stories = parser.parse_stories(str(md_file))
        assert len(stories) == 2

