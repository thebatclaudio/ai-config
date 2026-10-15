"""
agents_md_linter.py

Validate AGENTS.md ↔ filesystem consistency.

Checks (global layer at repo root, local layer under ai/):
- Every agents/*.md, commands/*.md, skills/*/SKILL.md, mcp/*.json has a registry entry.
- Every registry entry has a corresponding file.
- No orphan files or missing registrations.

MCP rows are matched by server name (first column) -> mcp/<name>.json.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple


class AgentsMdLinter:
    """Linter for AGENTS.md registry tables."""

    SECTION_MARKERS = {
        "agents": "## 3. Agent Registry",
        "commands": "## 4. Command Registry",
        "skills": "## 5. Skill Registry",
        "mcp": "## 6. MCP Server Registry",
    }

    # section -> glob patterns (relative to repo root), global + local layer.
    LAYOUT = {
        "agents": ("agents/*.md", "ai/agents/*.md"),
        "commands": ("commands/*.md", "ai/commands/*.md"),
        "skills": ("skills/*/SKILL.md", "ai/skills/*/SKILL.md", "skills/*/*.py", "ai/skills/*/*.py"),
        "mcp": ("mcp/*.json", "ai/mcp/*.json"),
    }
    PATH_RE = re.compile(r"^[\w./-]+/[\w.-]+\.(md|py|json)$")

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.agents_md_path = repo_root / "AGENTS.md"

    def lint(self) -> Dict[str, List[str]]:
        """
        Run all validation checks. Return dict with "errors", "warnings", "info".
        """
        result: Dict[str, List[str]] = {"errors": [], "warnings": [], "info": []}

        if not self.agents_md_path.exists():
            result["errors"].append("AGENTS.md not found")
            return result

        text = self.agents_md_path.read_text(encoding="utf-8")

        # Extract file references from tables
        global_files = self._extract_file_refs(text)

        # Collect actual files on disk
        actual_files = self._collect_actual_files()

        # Cross-reference
        for section, registered_files in global_files.items():
            actual = actual_files.get(section, set())
            missing = registered_files - actual
            orphans = actual - registered_files

            for f in sorted(missing):
                result["errors"].append(f"[{section}] Registry entry references {f} but file not found")
            for f in sorted(orphans):
                result["warnings"].append(f"[{section}] File {f} exists but no registry entry found")

        if not result["errors"] and not result["warnings"]:
            result["info"].append("AGENTS.md is consistent with the filesystem")

        return result

    def _extract_file_refs(self, text: str) -> Dict[str, set]:
        """Extract file references from AGENTS.md tables by section."""
        sections: Dict[str, set] = {
            "agents": set(),
            "commands": set(),
            "skills": set(),
            "mcp": set(),
        }

        current_section = None
        for line in text.split("\n"):
            # Detect section headers
            if line.startswith("## "):
                current_section = None
                for section, marker in self.SECTION_MARKERS.items():
                    if marker in line:
                        current_section = section
                        break

            # Skip table headers and separators
            if "| -----" in line or line.strip().startswith("| ---"):
                continue

            if current_section is None:
                continue

            if not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells or cells[0] in ("Name", "") or set(cells[0]) <= set("-: "):
                continue

            if current_section == "mcp":
                # | name | transport | ... |  -> mcp/<name>.json
                sections["mcp"].add(f"mcp/{cells[0].strip('`')}.json")
                continue

            # Any backtick token that looks like a path counts as a reference,
            # whether or not it exists (so missing files are reported).
            for match in re.findall(r"`([^`]+)`", line):
                if self.PATH_RE.match(match):
                    sections[current_section].add(match)

        return sections

    def _collect_actual_files(self) -> Dict[str, set]:
        """Collect actual files from the filesystem."""
        actual: Dict[str, set] = {
            "agents": set(),
            "commands": set(),
            "skills": set(),
            "mcp": set(),
        }

        for key, patterns in self.LAYOUT.items():
            for pattern in patterns:
                for path in self.repo_root.glob(pattern):
                    actual[key].add(path.relative_to(self.repo_root).as_posix())

        return actual


def main() -> None:
    """CLI entry point."""
    import sys
    linter = AgentsMdLinter(Path.cwd())
    results = linter.lint()

    for severity, messages in results.items():
        for msg in messages:
            prefix = {"errors": "ERROR", "warnings": "WARN", "info": "INFO"}[severity]
            print(f"[{prefix}] {msg}")

    if results.get("errors"):
        sys.exit(1)


if __name__ == "__main__":
    main()
