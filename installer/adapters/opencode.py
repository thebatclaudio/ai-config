"""
installer.adapters.opencode
===========================

OpenCode adapter.

Global (``~/.config/opencode`` or ``$OPENCODE_CONFIG_DIR`` / ``--opencode-dir``):
    * ``opencode.json``: render ``opencode.json.example`` and deep-merge
      (existing values win). Carries the ``instructions`` entry.
    * ``agent/``, ``command/``, ``skill/``, ``mcp/``: directory symlinks to the
      repo's canonical folders.

Local (``<repo>/.opencode/``, git-ignored): relative symlinks
``agent``, ``command``, ``skill`` -> ``../ai/{agents,commands,skills}``.

Phase 3 status: this reproduces the pre-refactor setup.py output exactly.
Phase 4 adds rendered agents (``mode: subagent``) and a real ``mcp`` block.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from ..catalog import Catalog
from ..core import (
    Report, ensure_symlink, load_json, merge_configs, remove_symlink_into,
    render_json_template, write_json,
)
from .base import Adapter

TEMPLATE = "opencode.json.example"
CONFIG_FILE = "opencode.json"

# repo folder -> OpenCode folder
GLOBAL_LINKS = {"agents": "agent", "commands": "command", "skills": "skill", "mcp": "mcp"}
LOCAL_LINKS = {"agents": "agent", "commands": "command", "skills": "skill"}
LOCAL_DIR = ".opencode"


class OpenCodeAdapter(Adapter):
    name = "opencode"
    label = "OpenCode"
    config_env_var = "OPENCODE_CONFIG_DIR"

    def detect(self) -> bool:
        return bool(shutil.which("opencode")) or self.default_config_dir().is_dir()

    def default_config_dir(self) -> Path:
        return (self.xdg_config_home() / "opencode").resolve()

    # -- global ------------------------------------------------------------

    def install_instructions(self, catalog: Catalog, report: Report) -> None:
        target = self.config_dir() / CONFIG_FILE
        generated = render_json_template(self.ctx.repo_root / TEMPLATE, self.ctx.env)
        merged, collisions = merge_configs(load_json(target), generated)
        report.collisions.extend(collisions)
        write_json(target, merged, self.ctx, report)

    def install_items(self, catalog: Catalog, report: Report) -> None:
        cfg = self.config_dir()
        for src, dst in GLOBAL_LINKS.items():
            ensure_symlink(self.ctx.repo_root / src, cfg / dst, self.ctx, report)

    def install_mcp(self, catalog: Catalog, report: Report) -> None:
        # Legacy behavior: the `mcp/` symlink above. OpenCode does not read it;
        # Phase 4 renders catalog.mcp into opencode.json -> "mcp".
        report.notes.append(
            f"MCP: {len(catalog.mcp)} servers in catalog, not yet rendered into "
            f"opencode.json (Phase 4)."
        )

    def uninstall(self) -> Report:
        cfg = self.config_dir()
        report = Report(target=f"{self.label} (global) -> {cfg}")
        for dst in GLOBAL_LINKS.values():
            remove_symlink_into(cfg / dst, self.ctx.repo_root, self.ctx, report)
        report.notes.append(f"{cfg / CONFIG_FILE} left in place (it may hold your own settings).")
        return report

    # -- local (ai/ layer) -------------------------------------------------

    def install_local(self) -> Report:
        root = self.ctx.repo_root
        report = Report(target=f"{self.label} (local) -> {root / LOCAL_DIR}")
        self._catalog("local", report)
        for src, dst in LOCAL_LINKS.items():
            ensure_symlink(root / "ai" / src, root / LOCAL_DIR / dst, self.ctx, report, relative=True)
        return report

    def uninstall_local(self) -> Report:
        root = self.ctx.repo_root
        report = Report(target=f"{self.label} (local) -> {root / LOCAL_DIR}")
        for dst in LOCAL_LINKS.values():
            remove_symlink_into(root / LOCAL_DIR / dst, root, self.ctx, report)
        return report
