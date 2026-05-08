"""
conventional_commit.py

Format, lint, and suggest Conventional Commits messages.
Follows: <type>(<scope>): <subject> [optional body] [optional footer]
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ConventionalCommit:
    """Parsed representation of a Conventional Commit message."""
    type: str  # feat, fix, docs, style, refactor, perf, test, chore, ci, revert
    scope: Optional[str]  # optional scope
    subject: str  # short description
    body: Optional[str] = None  # optional detailed message
    footers: List[Tuple[str, str]] = None  # optional footers (key-value pairs)

    def __post_init__(self):
        if self.footers is None:
            self.footers = []

    def to_string(self) -> str:
        """Reconstruct the full commit message."""
        header = f"{self.type}"
        if self.scope:
            header += f"({self.scope})"
        header += f": {self.subject}"

        parts = [header]
        if self.body:
            parts.append("")
            parts.append(self.body)
        if self.footers:
            parts.append("")
            for key, value in self.footers:
                parts.append(f"{key}: {value}")

        return "\n".join(parts)

    def is_breaking(self) -> bool:
        """Return True if this commit marks a breaking change."""
        if self.type == "revert":
            return True
        for key, _ in self.footers:
            if key.upper() in ("BREAKING CHANGE", "BREAKING-CHANGE"):
                return True
        return False


VALID_TYPES = {
    "feat",      # new feature
    "fix",       # bug fix
    "docs",      # documentation
    "style",     # formatting, missing semicolons, etc.
    "refactor",  # code refactor
    "perf",      # performance improvement
    "test",      # test changes
    "chore",     # build, deps, scripts, etc.
    "ci",        # CI/CD config
    "revert",    # revert a previous commit
}


def parse_commit_message(message: str) -> Optional[ConventionalCommit]:
    """
    Parse a commit message into a ConventionalCommit object.
    Returns None if the message doesn't follow Conventional Commits format.
    """
    lines = message.strip().split("\n", 1)
    header = lines[0]
    body_and_footers = lines[1] if len(lines) > 1 else ""

    # Parse header: type(scope): subject
    match = re.match(r"^(\w+)(?:\(([^)]+)\))?: (.+)$", header)
    if not match:
        return None

    commit_type, scope, subject = match.groups()
    if commit_type not in VALID_TYPES:
        return None

    # Parse body and footers (simple split)
    body = None
    footers: List[Tuple[str, str]] = []

    if body_and_footers:
        # Split into body and footer section
        sections = body_and_footers.split("\n\n")
        if len(sections) >= 1:
            body = sections[0].strip()
        if len(sections) >= 2:
            footer_section = sections[-1]
            for line in footer_section.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    footers.append((key.strip(), value.strip()))

    return ConventionalCommit(
        type=commit_type,
        scope=scope,
        subject=subject,
        body=body,
        footers=footers,
    )


def lint_commit_message(message: str) -> List[str]:
    """
    Lint a commit message. Return a list of issues (empty if valid).
    """
    issues = []

    lines = message.strip().split("\n", 1)
    header = lines[0]

    # Check header length (convention: max 50 chars)
    if len(header) > 72:
        issues.append(f"Header is too long ({len(header)} chars; recommend ≤ 72)")

    # Check format
    if not re.match(r"^\w+(?:\([^)]+\))?: .+", header):
        issues.append("Header does not follow 'type(scope): subject' format")
        return issues

    # Extract type
    match = re.match(r"^(\w+)", header)
    if match:
        commit_type = match.group(1)
        if commit_type not in VALID_TYPES:
            issues.append(f"Invalid type '{commit_type}'. Valid: {', '.join(sorted(VALID_TYPES))}")

    # Check for empty subject
    if re.match(r"^\w+(?:\([^)]+\))?: $", header):
        issues.append("Subject is empty")

    return issues


def suggest_commit_type(change_description: str) -> Tuple[str, float]:
    """
    Suggest a commit type based on a description. Returns (type, confidence).
    Confidence is 0.0–1.0 based on keyword matching.
    """
    keywords = {
        "feat": ["add", "new", "implement", "feature"],
        "fix": ["fix", "bug", "patch", "resolve", "issue"],
        "docs": ["doc", "readme", "comment", "documentation"],
        "style": ["format", "style", "semicolon", "indent"],
        "refactor": ["refactor", "reorganize", "rename", "extract"],
        "perf": ["perf", "performance", "optimize", "speed", "faster"],
        "test": ["test", "spec", "coverage"],
        "chore": ["deps", "dependency", "bump", "update", "script"],
    }

    lower_desc = change_description.lower()
    scores = {}

    for commit_type, kws in keywords.items():
        score = sum(1 for kw in kws if kw in lower_desc)
        scores[commit_type] = score

    if max(scores.values()) == 0:
        return "chore", 0.3  # default low-confidence guess

    best_type = max(scores, key=scores.get)
    confidence = scores[best_type] / len(keywords[best_type])
    return best_type, min(confidence, 1.0)
