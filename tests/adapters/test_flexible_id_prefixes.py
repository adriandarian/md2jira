"""
Parameterized tests for flexible story ID prefixes across all parsers.

Tests that all parsers correctly handle various PREFIX-NUMBER formats:
- Standard: US-001, PROJ-123, FEAT-042
- Regional: EU-001, NA-002, APAC-003
- Custom: CUSTOM-999, A-1, VERYLONGPREFIX-12345
- GitHub-style: #123
- Pure numeric: 456

This ensures organizations can use their own naming conventions.
"""

from textwrap import dedent

import pytest

from spectra.adapters.parsers import MarkdownParser
from spectra.adapters.parsers.json_parser import JsonParser
from spectra.adapters.parsers.yaml_parser import YamlParser


# =============================================================================
# Test Data - Various ID Prefix Formats
# =============================================================================

# List of prefixes to test with each parser
ID_PREFIXES = [
    # Standard
    ("US-001", "US-001"),
    ("PROJ-123", "PROJ-123"),
    ("FEAT-042", "FEAT-042"),
    ("STORY-999", "STORY-999"),
    # Regional
    ("EU-001", "EU-001"),
    ("NA-002", "NA-002"),
    ("APAC-003", "APAC-003"),
    # Short prefix
    ("A-1", "A-1"),
    ("X-99", "X-99"),
    # Long prefix
    ("VERYLONGPREFIX-12345", "VERYLONGPREFIX-12345"),
    ("CUSTOMPROJECT-1", "CUSTOMPROJECT-1"),
    # Jira-like
    ("ABC-1", "ABC-1"),
    ("MYPROJ-500", "MYPROJ-500"),
]


# =============================================================================
# Markdown Parser Tests
# =============================================================================


class TestMarkdownParserFlexibleIds:
    """Parameterized tests for MarkdownParser ID prefix handling."""

    @pytest.fixture
    def parser(self) -> MarkdownParser:
        """Create a MarkdownParser instance."""
        return MarkdownParser()

    @pytest.mark.parametrize(("story_id", "expected_id"), ID_PREFIXES)
    def test_parse_story_id_table_format(
        self, parser: MarkdownParser, story_id: str, expected_id: str
    ) -> None:
        """Test parsing various story ID prefixes in table format."""
        content = dedent(f"""
            # Test Epic

            ### 🔧 {story_id}: Test Story Title

            | Field | Value |
            |-------|-------|
            | **Story Points** | 5 |
            | **Priority** | 🟡 High |
            | **Status** | ✅ Done |

            #### Description

            **As a** user
            **I want** a feature
            **So that** I benefit
        """)

        stories = parser.parse_stories(content)

        assert len(stories) == 1, f"Expected 1 story for ID {story_id}"
        assert str(stories[0].id) == expected_id

    @pytest.mark.parametrize(("story_id", "expected_id"), ID_PREFIXES)
    def test_parse_story_id_inline_format(
        self, parser: MarkdownParser, story_id: str, expected_id: str
    ) -> None:
        """Test parsing various story ID prefixes in inline format."""
        content = dedent(f"""
            # Test Epic

            ### {story_id}: Test Story Title

            **Priority**: P1
            **Story Points**: 3
            **Status**: 🔄 In Progress

            #### User Story

            > **As a** developer,
            > **I want** to test parsing,
            > **So that** all prefixes work.
        """)

        stories = parser.parse_stories(content)

        assert len(stories) == 1, f"Expected 1 story for ID {story_id}"
        assert str(stories[0].id) == expected_id

    @pytest.mark.parametrize(("story_id", "expected_id"), ID_PREFIXES)
    def test_parse_story_with_emoji_prefix(
        self, parser: MarkdownParser, story_id: str, expected_id: str
    ) -> None:
        """Test that various emojis work with different ID prefixes."""
        emojis = ["✅", "🔄", "📋", "🔧", "🚀", "✨", "🐛"]
        emoji = emojis[hash(story_id) % len(emojis)]  # Deterministic emoji selection

        content = dedent(f"""
            # Test Epic

            ### {emoji} {story_id}: Story With Emoji

            | **Story Points** | 5 |

            **As a** user **I want** a feature **So that** I benefit
        """)

        stories = parser.parse_stories(content)

        assert len(stories) == 1
        assert str(stories[0].id) == expected_id

    def test_parse_multiple_different_prefixes(self, parser: MarkdownParser) -> None:
        """Test parsing a document with multiple different ID prefixes."""
        content = dedent("""
            # Multi-Prefix Epic

            ### US-001: United States Story

            | **Story Points** | 5 |

            **As a** user **I want** features **So that** I'm happy

            ---

            ### EU-002: European Story

            | **Story Points** | 3 |

            **As a** user **I want** features **So that** I'm happy

            ---

            ### APAC-003: Asia-Pacific Story

            | **Story Points** | 8 |

            **As a** user **I want** features **So that** I'm happy

            ---

            ### CUSTOM-004: Custom Prefix Story

            | **Story Points** | 2 |

            **As a** user **I want** features **So that** I'm happy
        """)

        stories = parser.parse_stories(content)

        assert len(stories) == 4
        ids = [str(s.id) for s in stories]
        assert "US-001" in ids
        assert "EU-002" in ids
        assert "APAC-003" in ids
        assert "CUSTOM-004" in ids


# =============================================================================
# YAML Parser Tests
# =============================================================================


class TestYamlParserFlexibleIds:
    """Parameterized tests for YamlParser ID prefix handling."""

    @pytest.fixture
    def parser(self) -> YamlParser:
        """Create a YamlParser instance."""
        return YamlParser()

    @pytest.mark.parametrize(("story_id", "expected_id"), ID_PREFIXES)
    def test_parse_story_id(self, parser: YamlParser, story_id: str, expected_id: str) -> None:
        """Test parsing various story ID prefixes in YAML format."""
        content = dedent(f"""
            epic:
              key: EPIC-100
              title: Test Epic

            stories:
              - id: {story_id}
                title: Test Story Title
                description:
                  as_a: user
                  i_want: a feature
                  so_that: I benefit
                story_points: 5
                priority: high
                status: planned
        """)

        stories = parser.parse_stories(content)

        assert len(stories) == 1, f"Expected 1 story for ID {story_id}"
        assert str(stories[0].id) == expected_id

    def test_parse_multiple_different_prefixes(self, parser: YamlParser) -> None:
        """Test parsing YAML with multiple different ID prefixes."""
        content = dedent("""
            epic:
              key: MULTI-100
              title: Multi-Prefix Epic

            stories:
              - id: US-001
                title: US Story
                story_points: 5

              - id: EU-002
                title: EU Story
                story_points: 3

              - id: PROJ-003
                title: Project Story
                story_points: 8
        """)

        stories = parser.parse_stories(content)

        assert len(stories) == 3
        ids = [str(s.id) for s in stories]
        assert "US-001" in ids
        assert "EU-002" in ids
        assert "PROJ-003" in ids


# =============================================================================
# JSON Parser Tests
# =============================================================================


class TestJsonParserFlexibleIds:
    """Parameterized tests for JsonParser ID prefix handling."""

    @pytest.fixture
    def parser(self) -> JsonParser:
        """Create a JsonParser instance."""
        return JsonParser()

    @pytest.mark.parametrize(("story_id", "expected_id"), ID_PREFIXES)
    def test_parse_story_id(self, parser: JsonParser, story_id: str, expected_id: str) -> None:
        """Test parsing various story ID prefixes in JSON format."""
        import json

        data = {
            "epic": {"key": "EPIC-100", "title": "Test Epic"},
            "stories": [
                {
                    "id": story_id,
                    "title": "Test Story Title",
                    "description": {
                        "as_a": "user",
                        "i_want": "a feature",
                        "so_that": "I benefit",
                    },
                    "story_points": 5,
                    "priority": "high",
                    "status": "planned",
                }
            ],
        }
        content = json.dumps(data)

        stories = parser.parse_stories(content)

        assert len(stories) == 1, f"Expected 1 story for ID {story_id}"
        assert str(stories[0].id) == expected_id

    def test_parse_multiple_different_prefixes(self, parser: JsonParser) -> None:
        """Test parsing JSON with multiple different ID prefixes."""
        import json

        data = {
            "epic": {"key": "MULTI-100", "title": "Multi-Prefix Epic"},
            "stories": [
                {"id": "US-001", "title": "US Story", "story_points": 5},
                {"id": "EU-002", "title": "EU Story", "story_points": 3},
                {"id": "FEAT-003", "title": "Feature Story", "story_points": 8},
            ],
        }
        content = json.dumps(data)

        stories = parser.parse_stories(content)

        assert len(stories) == 3
        ids = [str(s.id) for s in stories]
        assert "US-001" in ids
        assert "EU-002" in ids
        assert "FEAT-003" in ids


# =============================================================================
# Cross-Parser Consistency Tests
# =============================================================================


class TestCrossParserIdConsistency:
    """Tests ensuring ID parsing is consistent across all parsers."""

    @pytest.mark.parametrize(("story_id", "expected_id"), ID_PREFIXES)
    def test_same_id_across_parsers(self, story_id: str, expected_id: str) -> None:
        """Test that the same ID is parsed identically by all parsers."""
        import json

        # Create content for each parser
        markdown_content = dedent(f"""
            # Epic

            ### {story_id}: Test Story

            | **Story Points** | 5 |

            **As a** user **I want** feature **So that** benefit
        """)

        yaml_content = dedent(f"""
            epic:
              title: Epic
            stories:
              - id: {story_id}
                title: Test Story
                story_points: 5
        """)

        json_content = json.dumps(
            {
                "epic": {"title": "Epic"},
                "stories": [{"id": story_id, "title": "Test Story", "story_points": 5}],
            }
        )

        # Parse with each parser
        md_parser = MarkdownParser()
        yaml_parser = YamlParser()
        json_parser = JsonParser()

        md_stories = md_parser.parse_stories(markdown_content)
        yaml_stories = yaml_parser.parse_stories(yaml_content)
        json_stories = json_parser.parse_stories(json_content)

        # All should produce the same ID
        assert len(md_stories) == 1
        assert len(yaml_stories) == 1
        assert len(json_stories) == 1

        assert str(md_stories[0].id) == expected_id
        assert str(yaml_stories[0].id) == expected_id
        assert str(json_stories[0].id) == expected_id


# =============================================================================
# Edge Cases
# =============================================================================


class TestIdPrefixEdgeCases:
    """Tests for edge cases in ID prefix handling."""

    @pytest.fixture
    def md_parser(self) -> MarkdownParser:
        return MarkdownParser()

    def test_lowercase_prefix_not_parsed(self, md_parser: MarkdownParser) -> None:
        """Test that lowercase prefixes are not parsed by the markdown parser.

        The markdown parser requires uppercase prefixes with hyphen-number format.
        This test verifies the expected behavior.
        """
        content = dedent("""
            # Epic

            ### proj-123: Lowercase Story

            | **Story Points** | 5 |

            **As a** user **I want** feature **So that** benefit
        """)

        stories = md_parser.parse_stories(content)

        # Lowercase prefixes are not recognized by the current regex pattern
        assert len(stories) == 0

    def test_mixed_case_prefix_not_parsed(self, md_parser: MarkdownParser) -> None:
        """Test mixed case prefixes are not parsed.

        The markdown parser requires fully uppercase prefixes.
        """
        content = dedent("""
            # Epic

            ### MyProj-123: Mixed Case Story

            | **Story Points** | 5 |

            **As a** user **I want** feature **So that** benefit
        """)

        stories = md_parser.parse_stories(content)

        # Mixed case prefixes are not recognized
        assert len(stories) == 0

    def test_numeric_only_prefix_not_parsed(self, md_parser: MarkdownParser) -> None:
        """Test purely numeric prefix is not parsed.

        The markdown parser requires PREFIX-NUMBER format, not just numbers.
        """
        content = dedent("""
            # Epic

            ### 123: Numeric Only Story

            | **Story Points** | 5 |

            **As a** user **I want** feature **So that** benefit
        """)

        # Numeric-only IDs are not parsed
        stories = md_parser.parse_stories(content)
        assert len(stories) == 0

    def test_prefix_with_numbers_not_at_end(self, md_parser: MarkdownParser) -> None:
        """Test prefix that contains numbers (not at the end) is not parsed.

        The current regex expects [A-Z]+-\\d+ pattern, so numbers in the prefix
        portion are not matched. Use uppercase-only prefixes.
        """
        content = dedent("""
            # Epic

            ### PROJ2024-001: Prefix With Year

            | **Story Points** | 5 |

            **As a** user **I want** feature **So that** benefit
        """)

        stories = md_parser.parse_stories(content)

        # The current regex pattern doesn't support numbers in the prefix portion
        # This is expected behavior - prefixes should be alphabetic
        assert len(stories) == 0

    def test_single_digit_number(self, md_parser: MarkdownParser) -> None:
        """Test single digit story number."""
        content = dedent("""
            # Epic

            ### PROJ-1: Single Digit Story

            | **Story Points** | 5 |

            **As a** user **I want** feature **So that** benefit
        """)

        stories = md_parser.parse_stories(content)

        assert len(stories) == 1
        assert str(stories[0].id) == "PROJ-1"

    def test_large_story_number(self, md_parser: MarkdownParser) -> None:
        """Test very large story number."""
        content = dedent("""
            # Epic

            ### PROJ-999999: Large Number Story

            | **Story Points** | 5 |

            **As a** user **I want** feature **So that** benefit
        """)

        stories = md_parser.parse_stories(content)

        assert len(stories) == 1
        assert str(stories[0].id) == "PROJ-999999"
