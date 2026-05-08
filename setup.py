#!/usr/bin/env python3
"""
ai-config / setup.py
====================

Self-configuring bootstrap for the OpenCode runtime.

What this script does:
    1. Loads variables from `.env` (warning loudly if only `.env.example` exists).
    2. Renders `opencode.json.example` by substituting `{{KEY}}` tokens with
       values from `.env`.
    3. Deep-merges the rendered template into the live OpenCode config
       (`~/.config/opencode/opencode.json` on Linux/macOS,
       `%APPDATA%\\opencode\\opencode.json` on Windows). On collisions,
       EXISTING values are preserved; the discarded template values are
       reported in the end-of-run recap.
    4. Creates symbolic links from this repository's plural folders into the
       OpenCode singular paths (`agent`, `command`, `skill`, `mcp`).
    5. Prints a recap with `[OK] / [SKIP] / [WARN] / [ERROR]` markers.

Cross-platform:
    Uses `pathlib`, `platform`, and explicit error handling for the well-known
    Windows symlink permission issue (WinError 1314). Falls back to NTFS
    directory junctions for directories when symlink creation is denied.

Idempotent:
    Re-running the script is safe. Symlinks already pointing to the correct
    target are skipped; existing real directories are backed up before being
    replaced.

Usage:
    python setup.py                 # generate config + symlinks
    python setup.py --dry-run       # show what would happen, change nothing
    python setup.py --force         # overwrite existing real files/dirs
    python setup.py --uninstall     # remove only the symlinks pointing into this repo
    python setup.py --opencode-dir /custom/path
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Mapping: local plural folder name  ->  OpenCode singular folder name.
SYMLINK_MAP: Dict[str, str] = {
    "agents": "agent",
    "commands": "command",
    "skills": "skill",
    "mcp": "mcp",
}

TEMPLATE_FILENAME = "opencode.json.example"
GENERATED_FILENAME = "opencode.json"
ENV_FILENAME = ".env"
ENV_EXAMPLE_FILENAME = ".env.example"

# Regex matching {{KEY}} tokens (KEY = uppercase letters/digits/underscore).
TOKEN_RE = re.compile(r"\{\{\s*([A-Z_][A-Z0-9_]*)\s*\}\}")


# ---------------------------------------------------------------------------
# Pretty logging helpers
# ---------------------------------------------------------------------------

def _log(prefix: str, msg: str) -> None:
    print(f"{prefix} {msg}")


def log_ok(msg: str) -> None:
    _log("[OK]   ", msg)


def log_skip(msg: str) -> None:
    _log("[SKIP] ", msg)


def log_warn(msg: str) -> None:
    _log("[WARN] ", msg)


def log_error(msg: str) -> None:
    _log("[ERROR]", msg)


def log_info(msg: str) -> None:
    _log("[INFO] ", msg)


# ---------------------------------------------------------------------------
# CLI parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap ai-config into the local OpenCode runtime.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned actions without modifying anything.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing real files/directories at symlink targets "
             "(originals are backed up).",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove symlinks created by this script (only those pointing "
             "into this repository).",
    )
    parser.add_argument(
        "--opencode-dir",
        type=str,
        default=None,
        help="Override the OpenCode config directory. "
             "Highest precedence (beats $OPENCODE_CONFIG_DIR and platform default).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def find_repo_root() -> Path:
    """Absolute path of the directory containing this script."""
    return Path(__file__).resolve().parent


def locate_opencode_config_dir(
    cli_override: str | None,
    env_override: str | None,
) -> Path:
    """
    Resolve the OpenCode config directory using this precedence:
        1. --opencode-dir CLI flag
        2. OPENCODE_CONFIG_DIR (from .env or process env)
        3. Platform default
            - Linux/macOS: ~/.config/opencode
            - Windows:     %APPDATA%\\opencode
    """
    if cli_override:
        return Path(cli_override).expanduser().resolve()

    if env_override:
        return Path(env_override).expanduser().resolve()

    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            # Fallback if APPDATA is somehow missing.
            appdata = str(Path.home() / "AppData" / "Roaming")
        return Path(appdata) / "opencode"

    # Linux, macOS, *BSD, etc.
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return (base / "opencode").resolve()


# ---------------------------------------------------------------------------
# .env handling
# ---------------------------------------------------------------------------

def _parse_env_file(path: Path) -> Dict[str, str]:
    """
    Minimal .env parser using only stdlib.

    Handles:
      - KEY=value, KEY = value
      - Quoted values (single and double), including multiline.
      - Comments (#) and blank lines.
      - Export prefix (`export KEY=value`).

    Does NOT handle:
      - Variable expansion ($VAR or ${VAR} inside values).
      - Inline comments after values.
    """
    text = path.read_text(encoding="utf-8")
    values: Dict[str, str] = {}

    for line in text.split("\n"):
        line = line.strip()

        # Skip blank lines and full-line comments.
        if not line or line.startswith("#"):
            continue

        # Strip optional 'export' prefix.
        if line.startswith("export "):
            line = line[len("export "):].strip()

        # Split on first '='.
        if "=" not in line:
            continue
        key, _, raw_val = line.partition("=")
        key = key.strip()
        raw_val = raw_val.strip()

        # Strip surrounding quotes.
        if len(raw_val) >= 2 and raw_val[0] == raw_val[-1] and raw_val[0] in ("'", '"'):
            raw_val = raw_val[1:-1]

        if key:
            values[key] = raw_val

    return values


def ensure_env_file(repo_root: Path) -> Dict[str, str]:
    """
    Make sure `.env` exists. Load and return its values.
    Aborts with exit code 1 if `.env` is missing.
    """
    env_path = repo_root / ENV_FILENAME
    example_path = repo_root / ENV_EXAMPLE_FILENAME

    if not env_path.exists():
        log_error(f"`.env` not found at {env_path}")
        if example_path.exists():
            log_warn(
                f"Found `{ENV_EXAMPLE_FILENAME}` instead. Copy it and edit:"
            )
            log_warn(f"    cp {example_path} {env_path}")
        else:
            log_warn(
                f"Neither `.env` nor `{ENV_EXAMPLE_FILENAME}` exists in {repo_root}."
            )
        sys.exit(1)

    # Primary: use the stdlib-only parser (no external dependency needed).
    values = _parse_env_file(env_path)

    # Optional enhancement: if python-dotenv is available, prefer its
    # richer parser (handles variable expansion, inline comments, etc.).
    try:
        from dotenv import dotenv_values  # noqa: F811
        dotenv_vals = {k: v for k, v in dotenv_values(env_path).items() if v is not None}
        # Merge: dotenv values fill any gaps or resolve expansions.
        for k, v in dotenv_vals.items():
            existing = values.get(k)
            if not existing or existing.startswith("$"):
                values[k] = v
    except ImportError:
        pass  # stdlib-only mode is fine.

    # Default BASE_PROJECT_PATH to the repo root if missing/placeholder.
    base = values.get("BASE_PROJECT_PATH", "").strip()
    if not base or base.startswith("/absolute/path/to"):
        log_warn(
            f"BASE_PROJECT_PATH not set in `.env`; defaulting to {repo_root}"
        )
        values["BASE_PROJECT_PATH"] = str(repo_root)

    return values


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

def render_template(template_path: Path, env_values: Dict[str, str]) -> Dict[str, Any]:
    """
    Substitute every `{{KEY}}` token with the matching value from `env_values`,
    then parse the result as JSON.
    """
    if not template_path.exists():
        log_error(f"Template not found: {template_path}")
        sys.exit(1)

    raw = template_path.read_text(encoding="utf-8")
    missing: List[str] = []

    def _sub(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in env_values:
            missing.append(key)
            return match.group(0)
        # JSON-escape the value (handles backslashes, quotes, etc.).
        return json.dumps(env_values[key])[1:-1]

    rendered = TOKEN_RE.sub(_sub, raw)

    if missing:
        log_warn(
            "Unsubstituted tokens (left as-is): "
            + ", ".join(sorted(set(missing)))
        )

    try:
        return json.loads(rendered)
    except json.JSONDecodeError as exc:
        log_error(f"Rendered template is not valid JSON: {exc}")
        log_error("Rendered content was:\n" + rendered)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Existing config + merge
# ---------------------------------------------------------------------------

def load_existing_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log_warn(
            f"Existing {path.name} is not valid JSON ({exc}); treating as empty."
        )
        return {}


def merge_configs(
    existing: Dict[str, Any],
    generated: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Deep-merge `generated` into `existing`. EXISTING values win on collision.

    Behavior per type:
        - dicts      : recursive merge.
        - lists      : ordered union with dedup (existing first, then new
                       items from generated). Counted as a "merge", not a
                       collision.
        - scalars    : existing kept; if values differ, a collision is logged.

    Returns:
        merged_config, collisions_log (list of human-readable strings).
    """
    collisions: List[str] = []

    def _merge(
        cur_existing: Any,
        cur_generated: Any,
        path: str,
    ) -> Any:
        # Both dicts → recurse.
        if isinstance(cur_existing, dict) and isinstance(cur_generated, dict):
            out: Dict[str, Any] = dict(cur_existing)
            for key, gen_val in cur_generated.items():
                sub_path = f"{path}.{key}" if path else key
                if key in out:
                    out[key] = _merge(out[key], gen_val, sub_path)
                else:
                    out[key] = gen_val
            return out

        # Both lists → ordered union.
        if isinstance(cur_existing, list) and isinstance(cur_generated, list):
            merged: List[Any] = list(cur_existing)
            for item in cur_generated:
                if item not in merged:
                    merged.append(item)
            return merged

        # Type mismatch or scalar collision.
        if cur_existing != cur_generated:
            collisions.append(
                f"{path}: kept existing={cur_existing!r}, "
                f"discarded template={cur_generated!r}"
            )
        return cur_existing

    if not existing:
        return dict(generated), collisions

    merged = _merge(existing, generated, path="")
    return merged, collisions


# ---------------------------------------------------------------------------
# Atomic JSON writer + backup
# ---------------------------------------------------------------------------

def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write_opencode_json(
    target_dir: Path,
    config: Dict[str, Any],
    dry_run: bool,
) -> Path | None:
    """
    Write `config` atomically to `<target_dir>/opencode.json`. Backs up any
    existing file. Returns the backup path (or None if no backup was needed).
    """
    target = target_dir / GENERATED_FILENAME
    backup_path: Path | None = None

    if dry_run:
        log_info(f"[dry-run] would write {target}")
        if target.exists():
            log_info(
                f"[dry-run] would back up existing {target} -> "
                f"{target}.bak.<timestamp>"
            )
        return None

    target_dir.mkdir(parents=True, exist_ok=True)

    # Backup existing file (don't touch existing symlinks — read through them).
    if target.exists():
        backup_path = target.with_suffix(target.suffix + f".bak.{_timestamp()}")
        shutil.copy2(target, backup_path)
        log_warn(f"Backed up existing config: {backup_path}")

    # Atomic write via tempfile in same dir + os.replace.
    with tempfile.NamedTemporaryFile(
        "w",
        delete=False,
        dir=str(target_dir),
        prefix=".opencode.",
        suffix=".json.tmp",
        encoding="utf-8",
    ) as tmp:
        json.dump(config, tmp, indent=2, ensure_ascii=False)
        tmp.write("\n")
        tmp_name = tmp.name

    os.replace(tmp_name, target)
    log_ok(f"Wrote {target}")
    return backup_path


# ---------------------------------------------------------------------------
# Symlink management
# ---------------------------------------------------------------------------

class SymlinkStats:
    """Tally counter passed through symlink operations for the final recap."""

    def __init__(self) -> None:
        self.created: List[str] = []
        self.skipped: List[str] = []
        self.replaced: List[str] = []
        self.backups: List[str] = []
        self.errors: List[str] = []


def _is_symlink_pointing_to(link: Path, expected: Path) -> bool:
    """Return True iff `link` is a symlink resolving to `expected`."""
    try:
        if not link.is_symlink():
            return False
        return Path(os.readlink(link)).resolve() == expected.resolve()
    except OSError:
        return False


def _windows_create_junction(src: Path, dst: Path) -> None:
    """
    Create an NTFS directory junction (no admin / Developer Mode required).
    Used as a fallback for directories on Windows when symlink fails.
    """
    # _winapi.CreateJunction is private but stable; available in CPython 3.x
    # on Windows. Use it only as a directory fallback.
    import _winapi  # type: ignore[attr-defined]

    if dst.exists() or dst.is_symlink():
        dst.unlink()
    _winapi.CreateJunction(str(src), str(dst))


def _create_one_symlink(
    src: Path,
    dst: Path,
    force: bool,
    dry_run: bool,
    stats: SymlinkStats,
) -> None:
    rel = f"{dst.name} -> {src}"

    if not src.exists():
        log_warn(f"Source missing, skipping: {src}")
        stats.skipped.append(rel)
        return

    # Existing correct symlink -> nothing to do.
    if dst.is_symlink() and _is_symlink_pointing_to(dst, src):
        log_skip(f"Symlink already correct: {rel}")
        stats.skipped.append(rel)
        return

    # Path exists in some form (broken symlink, real dir, real file).
    if dst.exists() or dst.is_symlink():
        if dst.is_symlink():
            # Wrong-target or broken symlink -> safe to remove.
            if dry_run:
                log_info(f"[dry-run] would remove stale symlink: {dst}")
            else:
                dst.unlink()
                log_warn(f"Removed stale symlink: {dst}")
        else:
            # Real file or real directory: require --force or back it up.
            if not force:
                log_warn(
                    f"Refusing to replace existing real path: {dst} "
                    f"(use --force to back up and replace)"
                )
                stats.skipped.append(rel)
                return

            backup = dst.with_name(dst.name + f".bak.{_timestamp()}")
            if dry_run:
                log_info(f"[dry-run] would back up {dst} -> {backup}")
            else:
                shutil.move(str(dst), str(backup))
                log_warn(f"Backed up real path: {dst} -> {backup}")
                stats.backups.append(str(backup))
            stats.replaced.append(rel)

    if dry_run:
        log_info(f"[dry-run] would create symlink: {rel}")
        stats.created.append(rel)
        return

    dst.parent.mkdir(parents=True, exist_ok=True)

    try:
        os.symlink(src, dst, target_is_directory=src.is_dir())
        log_ok(f"Created symlink: {rel}")
        stats.created.append(rel)
        return
    except OSError as exc:
        # Windows: WinError 1314 = SeCreateSymbolicLinkPrivilege missing.
        winerror = getattr(exc, "winerror", None)
        if platform.system() == "Windows" and winerror == 1314 and src.is_dir():
            log_warn(
                "Symlink creation denied (Windows requires Developer Mode "
                "or admin). Falling back to a directory junction."
            )
            try:
                _windows_create_junction(src, dst)
                log_ok(f"Created junction: {rel}")
                stats.created.append(rel)
                return
            except Exception as junction_exc:  # noqa: BLE001
                log_error(f"Junction fallback failed for {dst}: {junction_exc}")
                stats.errors.append(f"{rel} ({junction_exc})")
                return

        log_error(f"Failed to create symlink {rel}: {exc}")
        if platform.system() == "Windows":
            log_warn(
                "Hint: enable Developer Mode (Settings → Privacy & security "
                "→ For developers) or run this script from an elevated shell."
            )
        else:
            log_warn(
                f"Hint: check write permissions on {dst.parent}."
            )
        stats.errors.append(f"{rel} ({exc})")


def create_symlinks(
    repo_root: Path,
    target_dir: Path,
    force: bool,
    dry_run: bool,
) -> SymlinkStats:
    stats = SymlinkStats()

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    for local, opencode_name in SYMLINK_MAP.items():
        src = repo_root / local
        dst = target_dir / opencode_name
        _create_one_symlink(src, dst, force=force, dry_run=dry_run, stats=stats)

    return stats


# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------

def uninstall(
    repo_root: Path,
    target_dir: Path,
    dry_run: bool,
) -> None:
    """Remove only symlinks at OpenCode paths that point inside this repo."""
    log_info(f"Uninstalling symlinks under {target_dir}")
    repo_root_resolved = repo_root.resolve()

    for _, opencode_name in SYMLINK_MAP.items():
        dst = target_dir / opencode_name
        if not dst.is_symlink():
            log_skip(f"Not a symlink, leaving alone: {dst}")
            continue

        try:
            link_target = Path(os.readlink(dst)).resolve()
        except OSError as exc:
            log_warn(f"Could not read symlink {dst}: {exc}")
            continue

        if repo_root_resolved not in link_target.parents and link_target != repo_root_resolved:
            log_skip(
                f"Symlink does not point into this repo, leaving alone: "
                f"{dst} -> {link_target}"
            )
            continue

        if dry_run:
            log_info(f"[dry-run] would remove symlink {dst} -> {link_target}")
        else:
            dst.unlink()
            log_ok(f"Removed symlink {dst}")


# ---------------------------------------------------------------------------
# Recap
# ---------------------------------------------------------------------------

def print_recap(
    collisions: List[str],
    sym_stats: SymlinkStats,
    config_backup: Path | None,
    target_config: Path,
    dry_run: bool,
) -> None:
    print()
    print("=" * 72)
    print(" Setup recap" + (" (dry-run)" if dry_run else ""))
    print("=" * 72)

    log_ok(f"Symlinks created/updated: {len(sym_stats.created)}")
    for entry in sym_stats.created:
        print(f"         + {entry}")

    log_skip(f"Symlinks skipped: {len(sym_stats.skipped)}")
    for entry in sym_stats.skipped:
        print(f"         - {entry}")

    if sym_stats.replaced:
        log_warn(f"Symlinks replacing real paths: {len(sym_stats.replaced)}")
        for entry in sym_stats.replaced:
            print(f"         ! {entry}")

    if sym_stats.backups:
        log_warn(f"Backups created: {len(sym_stats.backups)}")
        for entry in sym_stats.backups:
            print(f"         > {entry}")

    if config_backup is not None:
        log_warn(f"Existing opencode.json backed up to: {config_backup}")

    log_info(f"Active opencode.json: {target_config}")

    if collisions:
        print()
        log_warn(
            f"Config merge collisions ({len(collisions)}) — EXISTING values were kept:"
        )
        for entry in collisions:
            print(f"         * {entry}")
        log_warn(
            "If you want template values, edit the active opencode.json by hand."
        )

    if sym_stats.errors:
        print()
        log_error(f"Errors encountered: {len(sym_stats.errors)}")
        for entry in sym_stats.errors:
            print(f"         x {entry}")

    print("=" * 72)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    repo_root = find_repo_root()

    log_info(f"Repository root: {repo_root}")
    log_info(f"Platform:        {platform.system()} ({platform.release()})")

    # Uninstall is independent of .env / template / merge.
    if args.uninstall:
        target_dir = locate_opencode_config_dir(
            cli_override=args.opencode_dir,
            env_override=os.environ.get("OPENCODE_CONFIG_DIR"),
        )
        log_info(f"OpenCode dir:    {target_dir}")
        uninstall(repo_root, target_dir, dry_run=args.dry_run)
        return 0

    # 1. Load .env.
    env_values = ensure_env_file(repo_root)

    # 2. Resolve OpenCode config dir (CLI > .env > platform default).
    target_dir = locate_opencode_config_dir(
        cli_override=args.opencode_dir,
        env_override=env_values.get("OPENCODE_CONFIG_DIR")
        or os.environ.get("OPENCODE_CONFIG_DIR"),
    )
    log_info(f"OpenCode dir:    {target_dir}")

    # 3. Render template.
    generated = render_template(repo_root / TEMPLATE_FILENAME, env_values)

    # 4. Merge with existing.
    existing = load_existing_config(target_dir / GENERATED_FILENAME)
    merged, collisions = merge_configs(existing, generated)

    # 5. Write merged config.
    config_backup = write_opencode_json(
        target_dir=target_dir,
        config=merged,
        dry_run=args.dry_run,
    )

    # 6. Create symlinks.
    sym_stats = create_symlinks(
        repo_root=repo_root,
        target_dir=target_dir,
        force=args.force,
        dry_run=args.dry_run,
    )

    # 7. Recap.
    print_recap(
        collisions=collisions,
        sym_stats=sym_stats,
        config_backup=config_backup,
        target_config=target_dir / GENERATED_FILENAME,
        dry_run=args.dry_run,
    )

    return 1 if sym_stats.errors else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log_error("Interrupted by user.")
        sys.exit(130)
