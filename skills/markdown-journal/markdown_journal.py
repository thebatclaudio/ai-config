"""
markdown_journal.py

Open and append daily markdown journal entries.
Provides a simple interface for the journal-coach agent.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional


class MarkdownJournal:
    """Simple markdown journal backed by daily .md files."""

    def __init__(self, root: Optional[Path] = None):
        """
        Initialize the journal.
        
        Args:
            root: Journal root directory. Defaults to ~/Documents/opencode/journal/
        """
        if root is None:
            root = Path.home() / "Documents" / "opencode" / "journal"
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _entry_path(self, date: Optional[datetime] = None) -> Path:
        """Get the path for a journal entry date."""
        if date is None:
            date = datetime.now()
        return self.root / f"{date.strftime('%Y-%m-%d')}.md"

    def today_path(self) -> Path:
        """Get the path for today's journal entry."""
        return self._entry_path()

    def create_today_entry(self, template: Optional[str] = None) -> str:
        """
        Create or read today's journal entry.
        If creating new, use a template. Return the file content.
        """
        path = self.today_path()

        if path.exists():
            return path.read_text(encoding="utf-8")

        # Create new entry with template
        if template is None:
            template = self._default_template()

        path.write_text(template, encoding="utf-8")
        return template

    def append_entry(self, content: str) -> None:
        """Append content to today's entry."""
        path = self.today_path()
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        path.write_text(existing + "\n" + content, encoding="utf-8")

    def get_entry(self, date: Optional[datetime] = None) -> Optional[str]:
        """Read an entry for a specific date (or today if None)."""
        path = self._entry_path(date)
        return path.read_text(encoding="utf-8") if path.exists() else None

    def list_entries(self, limit: int = 30) -> list:
        """List recent journal entries (most recent first)."""
        entries = sorted(self.root.glob("*.md"), reverse=True)
        return entries[:limit]

    def _default_template(self) -> str:
        """Default template for new journal entries."""
        today = datetime.now()
        return f"""# Journal — {today.strftime('%Y-%m-%d %A')}

## Reflections

_What are you feeling right now?_

## Gratitude

_Three things you're grateful for:_
- 
- 
- 

## Today's Focus

_What's the most important thing to focus on today?_

## Evening Review

_How did today go? What did you learn?_

"""
