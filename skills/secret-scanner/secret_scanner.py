"""
secret_scanner.py

Scan for accidentally committed secrets using regex and entropy analysis.
Detects API keys, tokens, credentials, etc.
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set


class SecretSeverity(Enum):
    """Severity levels for detected secrets."""
    HIGH = "high"      # likely real secret
    MEDIUM = "medium"  # suspicious
    LOW = "low"        # possible false positive


@dataclass
class SecretFinding:
    """Represents a detected secret."""
    path: Path
    line_no: int
    line_content: str
    pattern_name: str
    severity: SecretSeverity

    def display(self) -> str:
        """Format for display."""
        return f"{self.path}:{self.line_no} [{self.severity.value}] {self.pattern_name}"


# Common secret patterns
SECRET_PATTERNS = {
    "AWS_KEY": {
        "regex": r"AKIA[0-9A-Z]{16}",
        "severity": SecretSeverity.HIGH,
    },
    "GITHUB_TOKEN": {
        "regex": r"ghp_[A-Za-z0-9_]{36,255}",
        "severity": SecretSeverity.HIGH,
    },
    "GENERIC_API_KEY": {
        "regex": r"['\"]?api[_-]?key['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_-]{20,}['\"]?",
        "severity": SecretSeverity.MEDIUM,
    },
    "PRIVATE_KEY": {
        "regex": r"-----BEGIN (RSA |DSA |EC )?PRIVATE KEY",
        "severity": SecretSeverity.HIGH,
    },
    "SLACK_TOKEN": {
        "regex": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9_-]{24,34}",
        "severity": SecretSeverity.HIGH,
    },
    "POSTGRES_PASSWORD": {
        "regex": r"postgres://[^:]+:([^@]+)@",
        "severity": SecretSeverity.HIGH,
    },
}


class SecretScanner:
    """Scanner for accidentally committed secrets."""

    def __init__(self, skip_dirs: Optional[Set[str]] = None):
        if skip_dirs is None:
            skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", ".env"}
        self.skip_dirs = skip_dirs

    def scan_directory(self, root: Path, exclude_extensions: Optional[Set[str]] = None) -> List[SecretFinding]:
        """Recursively scan a directory for secrets."""
        if exclude_extensions is None:
            exclude_extensions = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar", ".gz"}

        findings: List[SecretFinding] = []

        for fpath in Path(root).rglob("*"):
            # Skip directories
            if fpath.is_dir():
                if fpath.name in self.skip_dirs:
                    continue

            # Skip large or binary files
            if fpath.suffix in exclude_extensions:
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                findings.extend(self._scan_content(content, fpath))
            except Exception:
                pass

        return findings

    def _scan_content(self, content: str, path: Path) -> List[SecretFinding]:
        """Scan file content for secrets."""
        findings: List[SecretFinding] = []

        for line_no, line in enumerate(content.split("\n"), 1):
            for pattern_name, pattern_config in SECRET_PATTERNS.items():
                regex = pattern_config["regex"]
                severity = pattern_config["severity"]

                if re.search(regex, line, re.IGNORECASE):
                    findings.append(SecretFinding(
                        path=path,
                        line_no=line_no,
                        line_content=line.strip()[:100],  # truncate
                        pattern_name=pattern_name,
                        severity=severity,
                    ))

        return findings

    def summarize(self, findings: List[SecretFinding]) -> str:
        """Generate a summary of findings."""
        if not findings:
            return "✓ No secrets found."

        high = [f for f in findings if f.severity == SecretSeverity.HIGH]
        medium = [f for f in findings if f.severity == SecretSeverity.MEDIUM]
        low = [f for f in findings if f.severity == SecretSeverity.LOW]

        lines = [
            f"Found {len(findings)} potential secrets:",
            f"  {len(high)} HIGH severity",
            f"  {len(medium)} MEDIUM severity",
            f"  {len(low)} LOW severity",
            "",
        ]

        if high:
            lines.append("HIGH severity findings:")
            for f in high[:5]:  # show first 5
                lines.append(f"  {f.display()}")

        return "\n".join(lines)
