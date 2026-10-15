"""
installer.migrations
====================

Tool-agnostic, idempotent housekeeping run before the adapters:

* Move personal data from the old OpenCode-named locations to the
  tool-neutral ai-config ones (see AGENTS.md section 2).
* Make sure data directories that MCP servers expect exist.

Safety rules: never overwrite. If both old and new exist, warn and leave
both alone. Copies are checksum-verified before the old path is removed.
"""

from __future__ import annotations

import filecmp
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from .core import Context, Report, log_info, log_ok, log_skip, log_warn

# (old, new) relative to $HOME.
DATA_MOVES: List[Tuple[str, str]] = [
    ("Documents/opencode/journal", "Documents/ai-config/journal"),
    ("Documents/opencode/budget", "Documents/ai-config/budget"),
    (".config/opencode/personal/feeds.toml", ".config/ai-config/feeds.toml"),
    (".local/share/opencode/memory/store.json", ".local/share/ai-config/memory/store.json"),
]

# Old parent folders to remove once empty.
OLD_PARENTS = ["Documents/opencode", ".config/opencode/personal", ".local/share/opencode/memory"]

ENSURE_DIRS = [".local/share/ai-config/memory", ".config/ai-config"]


def _same_tree(a: Path, b: Path) -> bool:
    if a.is_file():
        return b.is_file() and filecmp.cmp(a, b, shallow=False)
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    _, mismatch, errors = filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)
    if mismatch or errors:
        return False
    return all(_same_tree(a / d, b / d) for d in cmp.common_dirs)


def _move(old: Path, new: Path, ctx: Context, report: Report) -> None:
    if not old.exists():
        return
    if old.is_symlink():
        msg = f"{old} is a symlink; leaving it alone. Point it at {new} or move the data by hand."
        log_warn(msg)
        report.notes.append(msg)
        return
    if new.exists():
        msg = f"Both {old} and {new} exist; leaving both alone. Merge them by hand."
        log_warn(msg)
        report.notes.append(msg)
        return
    if ctx.dry_run:
        log_info(f"[dry-run] would move {old} -> {new}")
        report.created.append(f"{new} (moved from {old})")
        return
    new.parent.mkdir(parents=True, exist_ok=True)
    if old.is_dir():
        shutil.copytree(old, new, symlinks=True, copy_function=shutil.copy2)
    else:
        shutil.copy2(old, new)
    if not _same_tree(old, new):
        msg = f"Verification failed copying {old} -> {new}; kept the original."
        log_warn(msg)
        report.errors.append(msg)
        return
    shutil.rmtree(old) if old.is_dir() else old.unlink()
    log_ok(f"Moved {old} -> {new}")
    report.created.append(f"{new} (moved from {old})")


def run(ctx: Context, home: Optional[Path] = None) -> Report:
    """Run all data migrations. ``home`` is overridable for tests."""
    home = Path(home) if home else Path.home()
    report = Report(target="data (tool-neutral)")

    for old, new in DATA_MOVES:
        _move(home / old, home / new, ctx, report)

    if not ctx.dry_run:
        for parent in OLD_PARENTS:
            p = home / parent
            if p.is_dir() and not any(p.iterdir()):
                p.rmdir()
                log_ok(f"Removed empty legacy folder {p}")

    for d in ENSURE_DIRS:
        p = home / d
        if p.is_dir():
            continue
        if ctx.dry_run:
            log_info(f"[dry-run] would create {p}")
        else:
            p.mkdir(parents=True, exist_ok=True)
            log_ok(f"Created {p}")
        report.created.append(str(p))

    if not report.created and not report.notes and not report.errors:
        log_skip("Data locations already up to date")
        report.skipped.append("all data locations")
    return report
