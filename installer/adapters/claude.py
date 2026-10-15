"""
installer.adapters.claude
=========================

Claude Code adapter.

Global (``~/.claude`` or ``$CLAUDE_CONFIG_DIR`` / ``--claude-dir``):
    * ``CLAUDE.md``: a managed block importing the repo's ``AGENTS.md``
      (``@/abs/path/AGENTS.md``). Anything outside the block is yours.
    * ``agents/<name>.md``, ``commands/<name>.md``: per-item symlinks to files
      rendered into ``dist/claude/global/`` with Claude Code frontmatter.
    * ``skills/<name>``: per-item symlinks to the repo's skill folders.
    * MCP: ``claude mcp add-json --scope user``. A server that already exists
      with different settings is kept (reported as a collision) unless
      ``--force``. Without the ``claude`` CLI the commands are only printed.

Local (``<repo>/.claude/``, git-ignored):
    * ``agents``, ``commands`` -> ``../dist/claude/local/*``; ``skills`` -> ``../ai/skills``
    * ``CLAUDE.md`` importing ``ai/AGENTS.md`` (the local addendum).

Shared directories (``~/.claude/agents`` etc.) may hold your own files, so
only symlinks pointing into this repo are ever created or removed.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..catalog import Catalog, Item, McpServer, load_catalog
from ..core import (
    GENERATED_MARKER, Report, ensure_symlink, log_info, log_ok, log_skip, log_warn,
    remove_symlink_into, render_tokens, timestamp, write_text,
)
from .base import Adapter

LOCAL_DIR = ".claude"
DIST = Path("dist") / "claude"
BLOCK_BEGIN = "<!-- ai-config:begin"
BLOCK_END = "<!-- ai-config:end -->"
BLOCK_RE = re.compile(re.escape(BLOCK_BEGIN) + r".*?" + re.escape(BLOCK_END) + r"\n?", re.S)

# Canonical fields carried into Claude Code frontmatter (targets.claude overrides win).
AGENT_FIELDS = ("name", "description", "tools", "model")
COMMAND_FIELDS = ("description", "argument-hint", "allowed-tools", "model")

Runner = Callable[..., "subprocess.CompletedProcess[str]"]


def _yaml_value(value: Any) -> str:
    """Emit a frontmatter value. JSON strings are valid YAML double-quoted scalars."""
    if isinstance(value, list):
        return json.dumps(", ".join(str(v) for v in value), ensure_ascii=False)  # "Read, Grep"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)  # JSON is valid YAML flow
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def render_item(item: Item) -> str:
    """Render an agent or command as a Claude Code markdown file."""
    fields = AGENT_FIELDS if item.kind == "agent" else COMMAND_FIELDS
    meta: Dict[str, Any] = {k: item.meta[k] for k in fields if item.meta.get(k) is not None}
    meta.update(item.target("claude"))
    if meta.get("model") == "default":
        del meta["model"]
    lines = ["---"] + [f"{k}: {_yaml_value(v)}" for k, v in meta.items()] + ["---", ""]
    return "\n".join(lines) + item.body.lstrip("\n")


def managed_block(*imports: Path) -> str:
    body = "\n".join(f"@{p}" for p in imports)
    return f"{BLOCK_BEGIN} — {GENERATED_MARKER} -->\n{body}\n{BLOCK_END}\n"


class BrokenBlock(ValueError):
    """The begin/end markers are missing, duplicated or out of order."""


def block_state(text: str) -> str:
    """'none' (no markers), 'ok' (exactly one well-formed block) or 'broken'."""
    begins, ends = text.count(BLOCK_BEGIN), text.count(BLOCK_END)
    if begins == ends == 0:
        return "none"
    if begins == ends == 1 and text.index(BLOCK_BEGIN) < text.index(BLOCK_END):
        return "ok"
    return "broken"


def upsert_block(existing: str, block: str) -> str:
    state = block_state(existing)
    if state == "broken":
        raise BrokenBlock("ai-config markers are missing, duplicated or out of order")
    if state == "ok":
        return BLOCK_RE.sub(lambda _: block, existing, count=1)
    sep = "" if not existing or existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    return existing + sep + block


class ClaudeAdapter(Adapter):
    name = "claude"
    label = "Claude Code"
    config_env_var = "CLAUDE_CONFIG_DIR"

    def __init__(self, ctx, runner: Optional[Runner] = None) -> None:
        super().__init__(ctx)
        self.run_cli: Runner = runner or subprocess.run
        self.has_cli = runner is not None or bool(shutil.which("claude"))
        self.which: Callable[[str], Optional[str]] = shutil.which

    def detect(self) -> bool:
        return bool(shutil.which("claude")) or self.default_config_dir().is_dir()

    def default_config_dir(self) -> Path:
        return (Path.home() / ".claude").resolve()

    def _custom_dir(self) -> bool:
        return bool(self.ctx.overrides.get("claude_dir") or self.ctx.setting(self.config_env_var))

    def user_state_file(self) -> Path:
        """Where Claude Code keeps user-scope MCP servers."""
        if self._custom_dir():
            return self.config_dir() / ".claude.json"
        return Path.home() / ".claude.json"

    # -- rendering ---------------------------------------------------------

    def _render(self, catalog: Catalog) -> Dict[str, Dict[str, Path]]:
        """Render agents/commands into dist/claude/<scope>/; prune stale files."""
        out: Dict[str, Dict[str, Path]] = {}
        base = self.ctx.repo_root / DIST / catalog.scope
        for group in ("agents", "commands"):
            folder = base / group
            out[group] = {}
            for item in getattr(catalog, group):
                dst = folder / f"{item.name}.md"
                write_text(dst, render_item(item), self.ctx, Report(target="dist"))
                out[group][item.name] = dst
            if folder.is_dir() and not self.ctx.dry_run:
                for stale in folder.glob("*.md"):
                    if stale.stem not in out[group]:
                        stale.unlink()
        return out

    def _owned(self, path: Path) -> bool:
        """True if ``path`` is a symlink pointing into this repo (ours to manage)."""
        if not path.is_symlink():
            return False
        target = Path(os.path.realpath(path))
        root = self.ctx.repo_root.resolve()
        return target == root or root in target.parents

    def _link(self, src: Path, dst: Path, report: Report, relative: bool = False) -> None:
        """Link ``dst`` -> ``src`` without ever replacing a path we don't own."""
        foreign = (dst.exists() or dst.is_symlink()) and not self._owned(dst)
        if foreign and not self.ctx.force:
            kind = "symlink" if dst.is_symlink() else "file/dir"
            msg = f"{dst}: your own {kind} is in the way, left alone (use --force to back it up and replace)"
            log_warn(msg)
            report.collisions.append(msg)
            return
        if foreign and dst.is_symlink():
            # --force: ensure_symlink would drop a symlink without a backup, so move it aside.
            backup = dst.with_name(dst.name + f".bak.{timestamp()}")
            if self.ctx.dry_run:
                log_info(f"[dry-run] would back up {dst} -> {backup}")
            else:
                dst.rename(backup)
                log_warn(f"Backed up your symlink: {dst} -> {backup}")
                report.backups.append(str(backup))
        # In a dry run dist/ files are not written yet; report the link anyway.
        if self.ctx.dry_run and not src.exists():
            log_info(f"[dry-run] would create symlink: {dst} -> {src}")
            report.created.append(f"{dst} -> {src}")
            return
        ensure_symlink(src, dst, self.ctx, report, relative=relative)

    def _link_items(self, wanted: Dict[str, Path], folder: Path, suffix: str, report: Report) -> None:
        """Per-item symlinks in a shared folder; drop our links no longer wanted."""
        for name, src in wanted.items():
            self._link(src, folder / f"{name}{suffix}", report)
        if folder.is_dir():
            keep = {f"{n}{suffix}" for n in wanted}
            for link in sorted(folder.iterdir()):
                if link.is_symlink() and link.name not in keep:
                    remove_symlink_into(link, self.ctx.repo_root, self.ctx, report)

    # -- global ------------------------------------------------------------

    def _write_block(self, target: Path, block: str, report: Report) -> None:
        """Insert/refresh the managed block, writing through a symlinked file."""
        if target.is_symlink():
            if not target.exists():
                report.collisions.append(f"{target}: broken symlink, left alone")
                return
            target = Path(os.path.realpath(target))
        existing = target.read_text(encoding="utf-8") if target.is_file() else ""
        try:
            updated = upsert_block(existing, block)
        except BrokenBlock as exc:
            msg = f"{target}: {exc}; fix the markers by hand, file left alone"
            log_warn(msg)
            report.collisions.append(msg)
            return
        # Back up only when the file holds something besides our block.
        write_text(target, updated, self.ctx, report, backup=bool(BLOCK_RE.sub("", existing).strip()))

    def install_instructions(self, catalog: Catalog, report: Report) -> None:
        self._write_block(self.config_dir() / "CLAUDE.md",
                          managed_block(self.ctx.repo_root / "AGENTS.md"), report)

    def install_items(self, catalog: Catalog, report: Report) -> None:
        cfg = self.config_dir()
        rendered = self._render(catalog)
        self._link_items(rendered["agents"], cfg / "agents", ".md", report)
        self._link_items(rendered["commands"], cfg / "commands", ".md", report)
        self._link_items({s.name: s.path for s in catalog.skills}, cfg / "skills", "", report)

    # -- MCP -----------------------------------------------------------------

    def render_mcp(self, server: McpServer) -> Dict[str, Any]:
        """Canonical spec -> Claude Code JSON: tokens rendered, ~ expanded."""
        raw, missing = render_tokens(json.dumps(server.spec), self.ctx.env, json_escape=True)
        spec = json.loads(raw)
        if missing:
            log_warn(f"MCP {server.name}: unsubstituted tokens {', '.join(missing)}")

        def expand(v: str) -> str:
            v = os.path.expanduser(v)
            return os.path.normpath(v) if os.path.isabs(v) else v

        out: Dict[str, Any] = {"type": spec.get("type") or ("stdio" if "command" in spec else "http")}
        for key in ("command", "url"):
            if key in spec:
                out[key] = spec[key]
        if "args" in spec:
            out["args"] = [expand(a) for a in spec["args"]]
        if spec.get("env"):
            out["env"] = {k: expand(v) for k, v in spec["env"].items()}
        if spec.get("headers"):
            out["headers"] = spec["headers"]
        return out

    def _user_servers(self) -> Dict[str, Any]:
        path = self.user_state_file()
        try:
            return dict(json.loads(path.read_text(encoding="utf-8")).get("mcpServers") or {})
        except (OSError, json.JSONDecodeError):
            return {}

    def _cli(self, args: List[str], report: Report) -> bool:
        cmd = ["claude", "mcp", *args]
        shown = " ".join(cmd[:-1] + [f"'{cmd[-1]}'" if args[0] == "add-json" else cmd[-1]])
        if self.ctx.dry_run:
            log_info(f"[dry-run] would run: {shown}")
            return True
        env = dict(os.environ)
        if self._custom_dir():
            env["CLAUDE_CONFIG_DIR"] = str(self.config_dir())
        try:
            result = self.run_cli(cmd, capture_output=True, text=True, timeout=60, env=env)
        except (OSError, subprocess.TimeoutExpired) as exc:
            report.errors.append(f"{shown}: {exc}")
            return False
        if result.returncode != 0:
            report.errors.append(f"{shown}: {(result.stderr or result.stdout).strip()}")
            return False
        return True

    def _same(self, current: Dict[str, Any], wanted: Dict[str, Any]) -> bool:
        return all(current.get(k) == v for k, v in wanted.items())

    def install_mcp(self, catalog: Catalog, report: Report) -> None:
        current = self._user_servers()
        for server in catalog.mcp:
            spec = self.render_mcp(server)
            label = f"mcp {server.name}"
            existing = current.get(server.name)
            if existing is not None and self._same(existing, spec):
                log_skip(f"MCP server already registered: {server.name}")
                report.skipped.append(label)
                continue
            if existing is not None and not self.ctx.force:
                report.collisions.append(
                    f"{label}: kept existing user-scope server (use --force to replace it)")
                continue
            command = spec.get("command")
            if command and not self.which(command):
                report.notes.append(f"{label}: skipped, `{command}` not found on PATH")
                continue
            if not self.has_cli:
                report.notes.append(
                    f"claude CLI not found; run: claude mcp add-json --scope user "
                    f"{server.name} '{json.dumps(spec)}'")
                continue
            if existing is not None and not self._cli(["remove", "--scope", "user", server.name], report):
                continue
            if self._cli(["add-json", "--scope", "user", server.name, json.dumps(spec)], report):
                if not self.ctx.dry_run:
                    log_ok(f"Registered MCP server: {server.name}")
                report.created.append(label)

    def _uninstall_mcp(self, report: Report) -> None:
        catalog = load_catalog(self.ctx.repo_root, "global")
        current = self._user_servers()
        for server in catalog.mcp:
            existing = current.get(server.name)
            if existing is None:
                continue
            if not self._same(existing, self.render_mcp(server)):
                report.notes.append(f"mcp {server.name}: differs from the catalog, left in place")
                continue
            if self._cli(["remove", "--scope", "user", server.name], report):
                report.removed.append(f"mcp {server.name}")

    # -- uninstall -------------------------------------------------------------

    def _remove_block(self, target: Path, report: Report) -> None:
        if not target.is_file():
            return
        linked = target.is_symlink()
        real = Path(os.path.realpath(target))
        text = real.read_text(encoding="utf-8")
        state = block_state(text)
        if state == "none":
            return
        if state == "broken":
            report.collisions.append(f"{real}: ai-config markers are broken; file left alone")
            return
        remaining = BLOCK_RE.sub("", text)
        if remaining.strip() or linked:
            # Keep the file (and a symlinked file's target); back up user content.
            content = remaining.rstrip("\n") + "\n" if remaining.strip() else ""
            scratch = Report(target=report.target)
            write_text(real, content, self.ctx, scratch, backup=bool(remaining.strip()))
            report.backups.extend(scratch.backups)
        elif self.ctx.dry_run:
            log_info(f"[dry-run] would remove {target}")
        else:
            target.unlink()
            log_ok(f"Removed {target}")
        report.removed.append(str(target))

    def _unlink_all(self, folder: Path, report: Report) -> None:
        if folder.is_dir():
            for link in sorted(folder.iterdir()):
                if link.is_symlink():
                    remove_symlink_into(link, self.ctx.repo_root, self.ctx, report)

    def uninstall(self) -> Report:
        cfg = self.config_dir()
        report = Report(target=f"{self.label} (global) -> {cfg}")
        self._remove_block(cfg / "CLAUDE.md", report)
        for group in ("agents", "commands", "skills"):
            self._unlink_all(cfg / group, report)
        self._uninstall_mcp(report)
        return report

    # -- local (ai/ layer) -------------------------------------------------

    def install_local(self) -> Report:
        root = self.ctx.repo_root
        local = root / LOCAL_DIR
        report = Report(target=f"{self.label} (local) -> {local}")
        catalog = self._catalog("local", report)
        self._render(catalog)
        for group in ("agents", "commands"):
            self._link(root / DIST / "local" / group, local / group, report, relative=True)
        self._link(root / "ai" / "skills", local / "skills", report, relative=True)
        if (root / "ai" / "AGENTS.md").is_file():
            self._write_block(local / "CLAUDE.md", managed_block(Path("..") / "ai" / "AGENTS.md"), report)
        return report

    def uninstall_local(self) -> Report:
        root = self.ctx.repo_root
        local = root / LOCAL_DIR
        report = Report(target=f"{self.label} (local) -> {local}")
        for group in ("agents", "commands", "skills"):
            remove_symlink_into(local / group, root, self.ctx, report)
        self._remove_block(local / "CLAUDE.md", report)
        return report
