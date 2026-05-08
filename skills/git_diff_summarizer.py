"""
git_diff_summarizer.py

Parse and structure git diffs into consumable chunks for agents.
Handles multi-file diffs, hunks, language detection, and summary stats.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ChangeType(Enum):
    """Enum for change types in a diff."""
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    RENAMED = "renamed"


@dataclass
class Hunk:
    """Represents a single hunk (@@..@@) within a file diff."""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str]  # lines including +/- prefix

    def added_lines(self) -> List[str]:
        """Return lines that were added (starting with +)."""
        return [l[1:] for l in self.lines if l.startswith("+")]

    def removed_lines(self) -> List[str]:
        """Return lines that were removed (starting with -)."""
        return [l[1:] for l in self.lines if l.startswith("-")]


@dataclass
class FileDiff:
    """Represents a single file's diff."""
    path: str
    change_type: ChangeType
    old_path: Optional[str] = None  # for renames
    hunks: List[Hunk] = None
    is_binary: bool = False

    def __post_init__(self):
        if self.hunks is None:
            self.hunks = []

    def language(self) -> str:
        """Guess language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".sh": "bash",
        }
        for ext, lang in ext_map.items():
            if self.path.endswith(ext):
                return lang
        return "text"

    def summary(self) -> dict:
        """Return summary stats for this file."""
        total_added = sum(len(h.added_lines()) for h in self.hunks)
        total_removed = sum(len(h.removed_lines()) for h in self.hunks)
        return {
            "path": self.path,
            "language": self.language(),
            "type": self.change_type.value,
            "added_lines": total_added,
            "removed_lines": total_removed,
            "hunks": len(self.hunks),
        }


@dataclass
class DiffSummary:
    """Represents the complete parsed diff."""
    files: List[FileDiff]
    total_files_changed: int
    total_additions: int
    total_deletions: int

    def by_type(self, change_type: ChangeType) -> List[FileDiff]:
        """Filter files by change type."""
        return [f for f in self.files if f.change_type == change_type]


def parse_diff(diff_text: str) -> DiffSummary:
    """
    Parse a unified diff (git diff output) into structured FileDiff objects.
    """
    files: List[FileDiff] = []
    lines = diff_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect file header (---/+++ lines)
        if line.startswith("diff --git"):
            # Extract file paths
            match = re.match(r"diff --git a/(.*) b/(.*)", line)
            if not match:
                i += 1
                continue

            old_path, new_path = match.groups()
            change_type = ChangeType.MODIFIED
            i += 1

            # Look ahead for metadata
            while i < len(lines) and not lines[i].startswith("@@"):
                if lines[i].startswith("new file"):
                    change_type = ChangeType.ADDED
                elif lines[i].startswith("deleted file"):
                    change_type = ChangeType.DELETED
                elif lines[i].startswith("rename from"):
                    change_type = ChangeType.RENAMED
                i += 1

            # Parse hunks
            hunks: List[Hunk] = []
            while i < len(lines) and lines[i].startswith("@@"):
                hunk_match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", lines[i])
                if hunk_match:
                    old_start = int(hunk_match.group(1))
                    old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
                    new_start = int(hunk_match.group(3))
                    new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1

                    hunk_lines = []
                    i += 1
                    while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("diff"):
                        if lines[i] and lines[i][0] in ("+", "-", " "):
                            hunk_lines.append(lines[i])
                        i += 1

                    hunks.append(Hunk(old_start, old_count, new_start, new_count, hunk_lines))
                else:
                    i += 1

            files.append(FileDiff(new_path, change_type, old_path, hunks))
        else:
            i += 1

    # Calculate summary stats
    total_added = sum(sum(len(h.added_lines()) for h in f.hunks) for f in files)
    total_removed = sum(sum(len(h.removed_lines()) for h in f.hunks) for f in files)

    return DiffSummary(
        files=files,
        total_files_changed=len(files),
        total_additions=total_added,
        total_deletions=total_removed,
    )
