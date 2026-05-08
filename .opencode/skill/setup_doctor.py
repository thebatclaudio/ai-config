"""
setup_doctor.py

Health-check the ai-config setup.

Checks:
- .env file existence and required variables.
- opencode.json validity (if it exists).
- Symlink correctness (pointing to the right paths).
- setup.py compiles.
"""

import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class HealthReport:
    """Result of the health check."""
    passed: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return len(self.errors) == 0

    def print_report(self) -> None:
        """Print the health report."""
        for msg in self.passed:
            print(f"  [OK]  {msg}")
        for msg in self.warnings:
            print(f"  [WARN] {msg}")
        for msg in self.errors:
            print(f"  [ERROR] {msg}")

        print(f"\nHealthy: {'YES' if self.healthy else 'NO'}")
        return None


class SetupDoctor:
    """Diagnose the health of an ai-config installation."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        # Determine OpenCode config dir
        if platform.system() == "Windows":
            appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
            self.opencode_dir = Path(appdata) / "opencode"
        else:
            xdg = os.environ.get("XDG_CONFIG_HOME")
            base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
            self.opencode_dir = (base / "opencode").resolve()

    def check_env(self, report: HealthReport) -> None:
        """Check .env file."""
        env_path = self.repo_root / ".env"
        example_path = self.repo_root / ".env.example"

        if env_path.exists():
            report.passed.append(f".env found at {env_path}")
        elif example_path.exists():
            report.errors.append(f".env missing but .env.example exists. Run: cp {example_path} {env_path}")
        else:
            report.warnings.append("No .env or .env.example found")

    def check_opencode_json(self, report: HealthReport) -> None:
        """Check opencode.json validity."""
        paths = [
            self.repo_root / "opencode.json",
            self.repo_root / "opencode.json.example",
        ]

        for path in paths:
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                report.passed.append(f"{path.name}: valid JSON")
                if isinstance(data, dict) and "instructions" not in data:
                    report.warnings.append(f"{path.name}: missing 'instructions' key")
            except json.JSONDecodeError as exc:
                report.errors.append(f"{path.name}: invalid JSON — {exc}")

        generated = self.opencode_dir / "opencode.json"
        if generated.exists():
            try:
                json.loads(generated.read_text(encoding="utf-8"))
                report.passed.append(f"{generated}: valid JSON")
            except json.JSONDecodeError as exc:
                report.errors.append(f"{generated}: invalid JSON — {exc}")
        else:
            report.warnings.append(f"{generated}: not generated yet (run setup.py)")

    def check_symlinks(self, report: HealthReport) -> None:
        """Check that the symlinks are correct."""
        mapping = {
            "agent": "agents",
            "command": "commands",
            "skill": "skills",
            "mcp": "mcp",
        }

        for opencode_name, local_name in mapping.items():
            dst = self.opencode_dir / opencode_name
            src = self.repo_root / local_name

            if not dst.exists():
                report.warnings.append(f"Symlink {dst}: not found (run setup.py)")
                continue

            if not dst.is_symlink():
                report.warnings.append(f"{dst}: exists but is NOT a symlink")
                continue

            try:
                target = Path(os.readlink(str(dst))).resolve()
            except OSError as exc:
                report.errors.append(f"{dst}: cannot read symlink — {exc}")
                continue

            if not src.exists():
                report.errors.append(f"{src}: source does not exist")
                continue

            if target == src.resolve():
                report.passed.append(f"Symlink {opencode_name} -> {local_name}: correct")
            else:
                report.errors.append(
                    f"Symlink {opencode_name} points to {target}, expected {src.resolve()}"
                )

    def check_setup_py(self, report: HealthReport) -> None:
        """Check that setup.py compiles."""
        setup_path = self.repo_root / "setup.py"
        if not setup_path.exists():
            report.warnings.append("setup.py not found")
            return

        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(setup_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                report.passed.append("setup.py: compiles clean")
            else:
                report.errors.append(f"setup.py: compile error — {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            report.warnings.append("setup.py: compile check timed out")
        except Exception as exc:
            report.errors.append(f"setup.py: check failed — {exc}")

    def diagnose(self) -> HealthReport:
        """Run all checks and return the report."""
        report = HealthReport()
        self.check_env(report)
        self.check_opencode_json(report)
        self.check_symlinks(report)
        self.check_setup_py(report)
        return report


def main() -> None:
    """CLI entry point."""
    import sys

    doctor = SetupDoctor(Path.cwd())
    report = doctor.diagnose()
    report.print_report()
    sys.exit(0 if report.healthy else 1)


if __name__ == "__main__":
    main()
