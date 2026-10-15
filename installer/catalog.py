"""
installer.catalog
=================

Loads the canonical, tool-neutral sources of this repository into plain
objects that adapters render into each tool's native format.

    agents/*.md            -> Item(kind="agent")
    commands/*.md          -> Item(kind="command")
    skills/<name>/SKILL.md -> Item(kind="skill", path = skill folder)
    mcp/*.json             -> McpServer

The same layout under ``ai/`` is the *local* layer (this repo only).

Frontmatter is parsed by a small, dependency-free YAML subset parser so the
installer behaves identically on every machine (PyYAML is not required):

    key: "json-quoted string" | 'single quoted' | bare scalar
    key: [a, b, "c"]                      # flow list of scalars
    key: { a: 1, b: "x" }                 # flow map of scalars
    key:                                  # nested block (indented 2+ spaces)
      sub: value
    # comments and blank lines
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", re.S)
LAYERS = {"global": "", "local": "ai"}


# ---------------------------------------------------------------------------
# Frontmatter (YAML subset)
# ---------------------------------------------------------------------------

class FrontmatterError(ValueError):
    pass


def _split_flow(text: str) -> List[str]:
    """Split a flow collection body on top-level commas (quotes respected)."""
    parts, buf, quote, depth = [], [], None, 0
    for ch in text:
        if quote:
            buf.append(ch)
            if ch == quote and (len(buf) < 2 or buf[-2] != "\\"):
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def parse_scalar(raw: str) -> Any:
    s = raw.strip()
    if not s:
        return None
    if s[0] == '"':
        try:
            return json.loads(s)
        except json.JSONDecodeError as exc:
            raise FrontmatterError(f"bad double-quoted string: {s!r} ({exc})") from exc
    if s[0] == "'":
        if not s.endswith("'") or len(s) < 2:
            raise FrontmatterError(f"unterminated single-quoted string: {s!r}")
        return s[1:-1].replace("''", "'")
    if s[0] == "[":
        if not s.endswith("]"):
            raise FrontmatterError(f"unterminated flow list: {s!r}")
        return [parse_scalar(p) for p in _split_flow(s[1:-1])]
    if s[0] == "{":
        if not s.endswith("}"):
            raise FrontmatterError(f"unterminated flow map: {s!r}")
        out: Dict[str, Any] = {}
        for part in _split_flow(s[1:-1]):
            k, sep, v = part.partition(":")
            if not sep:
                raise FrontmatterError(f"flow map entry without ':': {part!r}")
            out[k.strip()] = parse_scalar(v)
        return out
    # Bare scalar: strip trailing " # comment".
    s = re.split(r"\s+#", s, maxsplit=1)[0].strip()
    lowered = s.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if lowered in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def parse_yaml_block(text: str) -> Dict[str, Any]:
    lines = [
        (len(line) - len(line.lstrip(" ")), line.strip())
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    def parse(start: int, indent: int) -> Tuple[Dict[str, Any], int]:
        out: Dict[str, Any] = {}
        i = start
        while i < len(lines):
            ind, content = lines[i]
            if ind < indent:
                break
            if ind > indent:
                raise FrontmatterError(f"unexpected indentation: {content!r}")
            key, sep, rest = content.partition(":")
            if not sep or not key.strip():
                raise FrontmatterError(f"expected 'key: value', got {content!r}")
            key = key.strip()
            if rest.strip():
                out[key] = parse_scalar(rest)
                i += 1
            elif i + 1 < len(lines) and lines[i + 1][0] > indent:
                out[key], i = parse(i + 1, lines[i + 1][0])
            else:
                out[key] = None
                i += 1
        return out, i

    data, _ = parse(0, lines[0][0] if lines else 0)
    return data


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """Return (frontmatter dict, body). No frontmatter -> ({}, text)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    return parse_yaml_block(m.group(1)), m.group(2)


# ---------------------------------------------------------------------------
# Catalog items
# ---------------------------------------------------------------------------

@dataclass
class Item:
    """An agent, command or skill from the canonical sources."""

    kind: str                 # agent | command | skill
    name: str
    scope: str                # global | local
    path: Path                # .md file (agent/command) or skill folder
    meta: Dict[str, Any]
    body: str

    @property
    def description(self) -> str:
        return str(self.meta.get("description") or "")

    @property
    def trigger(self) -> Optional[str]:
        return self.meta.get("trigger")

    @property
    def argument_hint(self) -> Optional[str]:
        return self.meta.get("argument-hint")

    def target(self, tool: str) -> Dict[str, Any]:
        """Per-tool overrides from ``targets.<tool>`` (may be empty)."""
        targets = self.meta.get("targets") or {}
        return dict(targets.get(tool) or {})


@dataclass
class McpServer:
    name: str
    scope: str
    path: Path
    spec: Dict[str, Any]      # command/args/env or url (canonical, un-rendered)


@dataclass
class Catalog:
    repo_root: Path
    scope: str
    agents: List[Item] = field(default_factory=list)
    commands: List[Item] = field(default_factory=list)
    skills: List[Item] = field(default_factory=list)
    mcp: List[McpServer] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def base(self) -> Path:
        sub = LAYERS[self.scope]
        return self.repo_root / sub if sub else self.repo_root

    def counts(self) -> str:
        return (f"{len(self.agents)} agents, {len(self.commands)} commands, "
                f"{len(self.skills)} skills, {len(self.mcp)} MCP servers")


def _load_item(path: Path, kind: str, scope: str, catalog: Catalog) -> Optional[Item]:
    md = path / "SKILL.md" if kind == "skill" else path
    expected = path.name if kind == "skill" else path.stem
    try:
        meta, body = parse_frontmatter(md.read_text(encoding="utf-8"))
    except (OSError, FrontmatterError) as exc:
        catalog.errors.append(f"{md}: {exc}")
        return None

    name = meta.get("name") or expected
    problems = []
    if name != expected:
        problems.append(f"name {name!r} != file/folder name {expected!r}")
    if meta.get("kind", kind) != kind:
        problems.append(f"kind {meta.get('kind')!r} != {kind!r}")
    if meta.get("scope", scope) != scope:
        problems.append(f"scope {meta.get('scope')!r} != {scope!r} (by location)")
    if not meta.get("description"):
        problems.append("missing description")
    if problems:
        catalog.errors.append(f"{md}: " + "; ".join(problems))
    return Item(kind=kind, name=name, scope=scope, path=path, meta=meta, body=body)


def load_catalog(repo_root: Path, scope: str = "global") -> Catalog:
    """Load one layer (``global`` = repo root, ``local`` = ``ai/``)."""
    catalog = Catalog(repo_root=Path(repo_root), scope=scope)
    base = catalog.base

    for kind, folder in (("agent", "agents"), ("command", "commands")):
        for path in sorted((base / folder).glob("*.md")):
            item = _load_item(path, kind, scope, catalog)
            if item:
                getattr(catalog, folder).append(item)

    for path in sorted((base / "skills").glob("*/SKILL.md")):
        item = _load_item(path.parent, "skill", scope, catalog)
        if item:
            catalog.skills.append(item)

    for path in sorted((base / "mcp").glob("*.json")):
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            catalog.errors.append(f"{path}: {exc}")
            continue
        if not ("command" in spec or "url" in spec):
            catalog.errors.append(f"{path}: needs 'command' (stdio) or 'url' (remote)")
            continue
        catalog.mcp.append(McpServer(name=path.stem, scope=scope, path=path, spec=spec))

    return catalog
