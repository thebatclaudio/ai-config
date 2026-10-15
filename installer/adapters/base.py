"""
installer.adapters.base
=======================

Contract every coding-tool adapter implements. An adapter converts the
canonical catalog (see ``installer.catalog``) into one tool's native layout.

Lifecycle for one run (``Adapter.install``):

    1. install_instructions(catalog, report)   # AGENTS.md / CLAUDE.md / config keys
    2. install_items(catalog, report)          # agents, commands, skills
    3. install_mcp(catalog, report)            # MCP server config

``install_local`` does the same for the ``ai/`` layer into the repo's own
project folder for that tool (e.g. ``.opencode/``), which is git-ignored.

Adding a tool = subclass ``Adapter``, implement the hooks, register it in
``installer/adapters/__init__.py``.
"""

from __future__ import annotations

import argparse
import os
import platform
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..catalog import Catalog, load_catalog
from ..core import Context, Report, log_info, log_warn


class Adapter(ABC):
    #: CLI/registry id, e.g. "opencode".
    name: str = ""
    #: Human label, e.g. "OpenCode".
    label: str = ""
    #: Env var (from .env or process) that overrides the config dir.
    config_env_var: str = ""

    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx

    # -- discovery ---------------------------------------------------------

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        """Register adapter-specific CLI flags (default: ``--<name>-dir``)."""
        parser.add_argument(
            f"--{cls.name}-dir", dest=f"{cls.name}_dir", default=None, metavar="PATH",
            help=f"Override the {cls.label} config directory "
                 f"(beats ${cls.config_env_var} and the platform default).",
        )

    @abstractmethod
    def detect(self) -> bool:
        """True if the tool appears to be installed/used on this machine."""

    @abstractmethod
    def default_config_dir(self) -> Path:
        """Platform default for the tool's user-level config directory."""

    def config_dir(self) -> Path:
        """CLI flag > env var (.env or process) > platform default."""
        override = self.ctx.overrides.get(f"{self.name}_dir")
        if override:
            return Path(override).expanduser().resolve()
        env_value = self.ctx.setting(self.config_env_var) if self.config_env_var else None
        if env_value:
            return Path(env_value).expanduser().resolve()
        return self.default_config_dir()

    # -- shared helpers ----------------------------------------------------

    @staticmethod
    def xdg_config_home() -> Path:
        if platform.system() == "Windows":
            return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        xdg = os.environ.get("XDG_CONFIG_HOME")
        return Path(xdg).expanduser() if xdg else Path.home() / ".config"

    def _catalog(self, scope: str, report: Report) -> Catalog:
        catalog = load_catalog(self.ctx.repo_root, scope)
        for err in catalog.errors:
            log_warn(f"[catalog] {err}")
            report.notes.append(f"catalog: {err}")
        log_info(f"{self.label}: {scope} layer has {catalog.counts()}")
        return catalog

    # -- lifecycle ---------------------------------------------------------

    def install(self) -> Report:
        report = Report(target=f"{self.label} (global) -> {self.config_dir()}")
        catalog = self._catalog("global", report)
        self.install_instructions(catalog, report)
        self.install_items(catalog, report)
        self.install_mcp(catalog, report)
        return report

    def install_local(self) -> Optional[Report]:
        """Install the ``ai/`` layer into this repo's project folder. Optional."""
        return None

    @abstractmethod
    def install_instructions(self, catalog: Catalog, report: Report) -> None: ...

    @abstractmethod
    def install_items(self, catalog: Catalog, report: Report) -> None: ...

    @abstractmethod
    def install_mcp(self, catalog: Catalog, report: Report) -> None: ...

    @abstractmethod
    def uninstall(self) -> Report:
        """Remove only what this installer created. Must be idempotent."""

    def uninstall_local(self) -> Optional[Report]:
        return None
