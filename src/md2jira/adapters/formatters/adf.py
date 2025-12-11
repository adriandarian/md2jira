"""
ADF Formatter - Atlassian Document Format for Jira.

Converts markdown and domain entities to Jira's ADF format.
"""

import re
from typing import Any

from ...core.ports.document_formatter import DocumentFormatterPort
from ...core.domain.entities import UserStory, Subtask
from ...core.domain.value_objects import CommitRef


class ADFFormatter(DocumentFormatterPort):
    """
    Atlassian Document Format formatter.
    
    Converts markdown/text to ADF for Jira API.
    Reference: https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/
    """
    
    @property
    def name(self) -> str:
        return "ADF"
    
    # -------------------------------------------------------------------------
    # DocumentFormatterPort Implementation
    # -------------------------------------------------------------------------
    
    def format_text(self, text: str) -> dict[str, Any]:
        """Convert markdown text to ADF."""
        content = []
        current_list = None
        current_list_type = None
        
        for line in text.split("\n"):
            if not line.strip():
                current_list = None
                current_list_type = None
                continue
            
            # Headings
            if line.startswith("### "):
                current_list = None
                content.append(self._heading(line[4:], level=3))
            elif line.startswith("## "):
                current_list = None
                content.append(self._heading(line[3:], level=2))
            elif line.startswith("# "):
                current_list = None
                content.append(self._heading(line[2:], level=1))
            
            # Jira wiki headings
            elif line.startswith("h3. "):
                current_list = None
                content.append(self._heading(line[4:], level=3))
            elif line.startswith("h2. "):
                current_list = None
                content.append(self._heading(line[4:], level=2))
            
            # Task list items
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
                    content.append(current_list)
                
                current_list["content"].append({
                    "type": "taskItem",
                    "attrs": {"localId": "", "state": "DONE" if is_checked else "TODO"},
                    "content": self._parse_inline(item_text)
                })
            
            # Bullet list
            elif line.startswith("* ") or (line.startswith("- ") and not line.startswith("- [")):
                item_text = line[2:]
                
                if current_list_type != 'bullet':
                    current_list = {"type": "bulletList", "content": []}
                    current_list_type = 'bullet'
                    content.append(current_list)
                
                current_list["content"].append({
                    "type": "listItem",
                    "content": [{"type": "paragraph", "content": self._parse_inline(item_text)}]
                })
            
            # Skip table rows
            elif line.startswith("|"):
                current_list = None
                current_list_type = None
                continue
            
            # Regular paragraph
            else:
                current_list = None
                current_list_type = None
                content.append({
                    "type": "paragraph",
                    "content": self._parse_inline(line)
                })
        
        return self._doc(content)
    
    def format_story_description(self, story: UserStory) -> dict[str, Any]:
        """Format a story's complete description."""
        return self.format_text(story.get_full_description())
    
    def format_subtask_description(self, subtask: Subtask) -> dict[str, Any]:
        """Format a subtask's description."""
        text = f"{subtask.description}\n\nStory Points: {subtask.story_points}"
        return self.format_text(text)
    
    def format_commits_table(self, commits: list[CommitRef]) -> dict[str, Any]:
        """Format commits as a table."""
        # Header row
        rows = [
            self._table_row([
                self._table_header("Commit"),
                self._table_header("Message"),
            ])
        ]
        
        # Data rows
        for commit in commits:
            rows.append(self._table_row([
                self._table_cell([self._code_text(commit.short_hash)]),
                self._table_cell([self._text(commit.message)]),
            ]))
        
        return self._doc([
            self._heading("Related Commits", level=3),
            {
                "type": "table",
                "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
                "content": rows
            }
        ])
    
    def format_heading(self, text: str, level: int = 2) -> dict[str, Any]:
        """Format a heading."""
        return self._doc([self._heading(text, level)])
    
    def format_list(self, items: list[str], ordered: bool = False) -> dict[str, Any]:
        """Format a list."""
        list_type = "orderedList" if ordered else "bulletList"
        list_items = []
        
        for item in items:
            list_items.append({
                "type": "listItem",
                "content": [{"type": "paragraph", "content": self._parse_inline(item)}]
            })
        
        return self._doc([{"type": list_type, "content": list_items}])
    
    def format_task_list(self, items: list[tuple[str, bool]]) -> dict[str, Any]:
        """Format a task/checkbox list."""
        task_items = []
        
        for text, is_checked in items:
            task_items.append({
                "type": "taskItem",
                "attrs": {"localId": "", "state": "DONE" if is_checked else "TODO"},
                "content": self._parse_inline(text)
            })
        
        return self._doc([{
            "type": "taskList",
            "attrs": {"localId": ""},
            "content": task_items
        }])
    
    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------
    
    def _doc(self, content: list) -> dict[str, Any]:
        """Create ADF document wrapper."""
        if not content:
            content = [{"type": "paragraph", "content": [{"type": "text", "text": " "}]}]
        
        return {
            "type": "doc",
            "version": 1,
            "content": content
        }
    
    def _heading(self, text: str, level: int = 2) -> dict[str, Any]:
        """Create heading node."""
        return {
            "type": "heading",
            "attrs": {"level": level},
            "content": [{"type": "text", "text": text}]
        }
    
    def _text(self, text: str) -> dict[str, Any]:
        """Create plain text node."""
        return {"type": "text", "text": text}
    
    def _bold_text(self, text: str) -> dict[str, Any]:
        """Create bold text node."""
        return {
            "type": "text",
            "text": text,
            "marks": [{"type": "strong"}]
        }
    
    def _code_text(self, text: str) -> dict[str, Any]:
        """Create inline code node."""
        return {
            "type": "text",
            "text": text,
            "marks": [{"type": "code"}]
        }
    
    def _italic_text(self, text: str) -> dict[str, Any]:
        """Create italic text node."""
        return {
            "type": "text",
            "text": text,
            "marks": [{"type": "em"}]
        }
    
    def _parse_inline(self, text: str) -> list[dict[str, Any]]:
        """Parse inline formatting: **bold**, *italic*, `code`."""
        content = []
        pattern = r'(\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`)'
        last_end = 0
        
        for match in re.finditer(pattern, text):
            # Add preceding text
            if match.start() > last_end:
                plain = text[last_end:match.start()]
                if plain:
                    content.append(self._text(plain))
            
            full = match.group(0)
            
            if full.startswith("**"):
                content.append(self._bold_text(match.group(2)))
            elif full.startswith("`"):
                content.append(self._code_text(match.group(4)))
            elif full.startswith("*"):
                content.append(self._italic_text(match.group(3)))
            
            last_end = match.end()
        
        # Add remaining text
        if last_end < len(text):
            remaining = text[last_end:]
            if remaining:
                content.append(self._text(remaining))
        
        return content if content else [self._text(text)]
    
    def _table_row(self, cells: list[dict]) -> dict[str, Any]:
        """Create table row."""
        return {"type": "tableRow", "content": cells}
    
    def _table_header(self, text: str) -> dict[str, Any]:
        """Create table header cell."""
        return {
            "type": "tableHeader",
            "attrs": {},
            "content": [{
                "type": "paragraph",
                "content": [self._bold_text(text)]
            }]
        }
    
    def _table_cell(self, content: list[dict]) -> dict[str, Any]:
        """Create table cell."""
        return {
            "type": "tableCell",
            "attrs": {},
            "content": [{
                "type": "paragraph",
                "content": content
            }]
        }

