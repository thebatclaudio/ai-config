#!/usr/bin/env python3
"""
ai-config / setup.py
====================

Install this repository's tool-neutral agents, commands, skills, MCP servers
and instructions into every AI coding tool you use.

Each tool has an adapter in ``installer/adapters/``; shared logic lives in
``installer/core.py``. Supported targets: see ``--target`` below.

What a run does:
    1. Loads `.env` (required for install).
    2. Moves personal data from legacy OpenCode-named paths to the
       tool-neutral ai-config ones (idempotent; never overwrites).
    3. For each target tool:
         - global layer (repo root)  -> the tool's user config dir
         - local layer  (ai/)        -> the tool's git-ignored project folder
    4. Prints a recap with [OK] / [SKIP] / [WARN] / [ERROR] markers.

Idempotent and cross-platform (Windows: junction fallback for directories).

Usage:
    python setup.py                         # auto-detect installed tools
    python setup.py --target opencode       # specific tool(s), comma-separated
    python setup.py --target all            # every supported tool
    python setup.py --layer global          # skip the local ai/ layer
    python setup.py --dry-run               # show what would happen
    python setup.py --force                 # back up & replace real dirs/files
    python setup.py --uninstall             # remove only what this installer created
    python setup.py --list                  # show the canonical catalog and exit
    python setup.py --opencode-dir PATH     # per-tool config dir override
    python setup.py --claude-dir PATH       #   (one flag per tool)
"""

from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path
from typing import List

from installer import migrations
from installer.adapters import ADAPTERS, Adapter
from installer.catalog import load_catalog
from installer.core import Context, Report, load_env, log_error, log_info, print_recap

REPO_ROOT = Path(__file__).resolve().parent


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install ai-config into your AI coding tools.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--target", default="auto",
        help="auto (default: detected tools) | all | comma list of: "
             + ", ".join(ADAPTERS),
    )
    parser.add_argument(
        "--layer", choices=("all", "global", "local"), default="all",
        help="global = repo root -> user config; local = ai/ -> this repo's "
             "tool folders (default: all).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Change nothing; show planned actions.")
    parser.add_argument("--force", action="store_true",
                        help="Replace existing real files/dirs at link targets (backed up first).")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove only links/files this installer created.")
    parser.add_argument("--list", action="store_true", help="Print the canonical catalog and exit.")
    parser.add_argument("--skip-migrate", action="store_true", help="Skip the data-location migration.")
    for adapter in ADAPTERS.values():
        adapter.add_arguments(parser)
    return parser.parse_args(argv)


def select_adapters(spec: str, ctx: Context) -> List[Adapter]:
    spec = spec.strip().lower()
    if spec == "all":
        return [cls(ctx) for cls in ADAPTERS.values()]
    if spec == "auto":
        found = [cls(ctx) for cls in ADAPTERS.values()]
        found = [a for a in found if a.detect()]
        if not found:
            log_error("No supported coding tool detected. Use --target " + ",".join(ADAPTERS))
            sys.exit(2)
        return found
    names = [n.strip() for n in spec.split(",") if n.strip()]
    unknown = [n for n in names if n not in ADAPTERS]
    if unknown:
        log_error(f"Unknown target(s): {', '.join(unknown)}. Supported: {', '.join(ADAPTERS)}")
        sys.exit(2)
    return [ADAPTERS[n](ctx) for n in names]


def print_catalog() -> int:
    rc = 0
    for scope in ("global", "local"):
        cat = load_catalog(REPO_ROOT, scope)
        print(f"\n[{scope}] {cat.base} — {cat.counts()}")
        for group in ("agents", "commands", "skills"):
            names = [i.trigger or i.name for i in getattr(cat, group)]
            print(f"  {group:9}: {', '.join(names) or '-'}")
        print(f"  {'mcp':9}: {', '.join(s.name for s in cat.mcp) or '-'}")
        for err in cat.errors:
            print(f"  [ERROR] {err}")
            rc = 1
    return rc


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list:
        return print_catalog()

    log_info(f"Repository root: {REPO_ROOT}")
    log_info(f"Platform:        {platform.system()} ({platform.release()})")

    env = load_env(REPO_ROOT, required=not args.uninstall)
    overrides = {f"{n}_dir": getattr(args, f"{n}_dir", None) for n in ADAPTERS}
    ctx = Context(repo_root=REPO_ROOT, env=env, dry_run=args.dry_run, force=args.force,
                  overrides=overrides)

    adapters = select_adapters(args.target, ctx)
    log_info("Targets:         " + ", ".join(a.label for a in adapters))

    reports: List[Report] = []
    do_global = args.layer in ("all", "global")
    do_local = args.layer in ("all", "local")

    if not args.uninstall and not args.skip_migrate:
        reports.append(migrations.run(ctx))

    for adapter in adapters:
        if args.uninstall:
            if do_global:
                reports.append(adapter.uninstall())
            if do_local and (r := adapter.uninstall_local()):
                reports.append(r)
        else:
            if do_global:
                log_info(f"--- {adapter.label}: global -> {adapter.config_dir()}")
                reports.append(adapter.install())
            if do_local:
                log_info(f"--- {adapter.label}: local (ai/)")
                if r := adapter.install_local():
                    reports.append(r)

    print_recap(reports, dry_run=args.dry_run)
    return 1 if any(r.errors for r in reports) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log_error("Interrupted by user.")
        sys.exit(130)
