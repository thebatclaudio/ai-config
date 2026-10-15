"""
Tests for the ai-config installer (stdlib unittest; pytest also runs them).

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from installer import migrations  # noqa: E402
from installer.adapters import ADAPTERS  # noqa: E402
from installer.adapters.claude import BrokenBlock, ClaudeAdapter, render_item, upsert_block  # noqa: E402
from installer.adapters.opencode import OpenCodeAdapter  # noqa: E402
from installer.catalog import FrontmatterError, load_catalog, parse_frontmatter  # noqa: E402
from installer.core import Context, merge_configs, render_tokens  # noqa: E402


def quiet():
    return contextlib.redirect_stdout(io.StringIO())


class FrontmatterTests(unittest.TestCase):
    def test_canonical_fields(self):
        meta, body = parse_frontmatter(
            '---\nname: x\nkind: agent\ndescription: "Say \\"hi\\" — ok"\n'
            'trigger: "@x"\n---\n# Body\n'
        )
        self.assertEqual(meta["description"], 'Say "hi" — ok')
        self.assertEqual(meta["trigger"], "@x")
        self.assertEqual(body, "# Body\n")

    def test_nested_targets_and_flow_collections(self):
        meta, _ = parse_frontmatter(
            "---\nname: x\ntools: [read, \"grep\", bash]\n"
            "targets:\n  opencode: { mode: subagent, temperature: 0.2 }\n"
            "  claude:\n    tools: \"Read, Grep\"\n    model: sonnet\n"
            "flag: true  # comment\n---\n"
        )
        self.assertEqual(meta["tools"], ["read", "grep", "bash"])
        self.assertEqual(meta["targets"]["opencode"], {"mode": "subagent", "temperature": 0.2})
        self.assertEqual(meta["targets"]["claude"], {"tools": "Read, Grep", "model": "sonnet"})
        self.assertIs(meta["flag"], True)

    def test_no_frontmatter(self):
        self.assertEqual(parse_frontmatter("# just text\n"), ({}, "# just text\n"))

    def test_errors(self):
        for bad in ('---\nname: "unterminated\n---\n', "---\nnot a pair\n---\n",
                    "---\nk: [a, b\n---\n"):
            with self.assertRaises(FrontmatterError, msg=bad):
                parse_frontmatter(bad)


class CatalogTests(unittest.TestCase):
    def test_repo_catalog_is_valid(self):
        for scope in ("global", "local"):
            cat = load_catalog(REPO, scope)
            self.assertEqual(cat.errors, [], f"{scope}: {cat.errors}")
            self.assertTrue(cat.agents and cat.commands and cat.skills, scope)
            for item in cat.agents + cat.commands:
                self.assertTrue(item.trigger, item.path)

    def test_global_has_all_mcp_servers(self):
        cat = load_catalog(REPO, "global")
        names = {s.name for s in cat.mcp}
        self.assertEqual(names, {p.stem for p in (REPO / "mcp").glob("*.json")})


class CoreTests(unittest.TestCase):
    def test_merge_existing_wins_and_lists_union(self):
        merged, collisions = merge_configs(
            {"a": 1, "l": [1], "d": {"x": 1}, "plugin": ["mine"]},
            {"a": 2, "l": [1, 2], "d": {"y": 2}, "new": True},
        )
        self.assertEqual(merged, {"a": 1, "l": [1, 2], "d": {"x": 1, "y": 2},
                                  "plugin": ["mine"], "new": True})
        self.assertEqual(len(collisions), 1)
        self.assertIn("a:", collisions[0])

    def test_render_tokens(self):
        out, missing = render_tokens('"{{A}}/{{ B }}"', {"A": 'C:\\x"'}, json_escape=True)
        self.assertEqual(out, '"C:\\\\x\\"/{{ B }}"')
        self.assertEqual(missing, ["B"])


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.ctx = Context(repo_root=REPO, env={})

    def tearDown(self):
        shutil.rmtree(self.home)

    def test_moves_data_and_is_idempotent(self):
        old = self.home / "Documents/opencode/budget/ledger.csv"
        old.parent.mkdir(parents=True)
        old.write_text("date,amount\n")
        with quiet():
            migrations.run(self.ctx, home=self.home)
        new = self.home / "Documents/ai-config/budget/ledger.csv"
        self.assertEqual(new.read_text(), "date,amount\n")
        self.assertFalse((self.home / "Documents/opencode").exists())
        self.assertTrue((self.home / ".local/share/ai-config/memory").is_dir())
        with quiet():
            report = migrations.run(self.ctx, home=self.home)
        self.assertEqual(report.created, [])

    def test_conflict_keeps_both(self):
        for root, text in (("opencode", "old"), ("ai-config", "new")):
            p = self.home / f"Documents/{root}/journal/2024-01-01.md"
            p.parent.mkdir(parents=True)
            p.write_text(text)
        with quiet():
            report = migrations.run(self.ctx, home=self.home)
        self.assertTrue(report.notes)
        self.assertEqual((self.home / "Documents/opencode/journal/2024-01-01.md").read_text(), "old")
        self.assertEqual((self.home / "Documents/ai-config/journal/2024-01-01.md").read_text(), "new")

    def test_symlinked_legacy_path_is_left_alone(self):
        real = self.home / "elsewhere/journal"
        real.mkdir(parents=True)
        (real / "2024-01-01.md").write_text("entry")
        old = self.home / "Documents/opencode/journal"
        old.parent.mkdir(parents=True)
        old.symlink_to(real)
        with quiet():
            report = migrations.run(self.ctx, home=self.home)
        self.assertTrue(report.notes)
        self.assertTrue(old.is_symlink())
        self.assertEqual((real / "2024-01-01.md").read_text(), "entry")
        self.assertFalse((self.home / "Documents/ai-config/journal").exists())

    def test_dry_run_changes_nothing(self):
        old = self.home / "Documents/opencode/journal"
        old.mkdir(parents=True)
        with quiet():
            migrations.run(Context(repo_root=REPO, env={}, dry_run=True), home=self.home)
        self.assertTrue(old.is_dir())
        self.assertFalse((self.home / "Documents/ai-config").exists())


class OpenCodeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.cfg = Path(tempfile.mkdtemp())
        self.ctx = Context(repo_root=REPO, env={"BASE_PROJECT_PATH": str(REPO)},
                           overrides={"opencode_dir": str(self.cfg)})

    def tearDown(self):
        shutil.rmtree(self.cfg)

    def test_registered(self):
        self.assertIs(ADAPTERS["opencode"], OpenCodeAdapter)

    def test_config_dir_precedence(self):
        a = OpenCodeAdapter(Context(repo_root=REPO, env={"OPENCODE_CONFIG_DIR": "/tmp/from-env"}))
        self.assertEqual(a.config_dir(), Path("/tmp/from-env"))
        self.assertEqual(OpenCodeAdapter(self.ctx).config_dir(), self.cfg.resolve())

    def test_install_preserves_user_keys_then_uninstall(self):
        (self.cfg / "opencode.json").write_text(json.dumps({"plugin": ["my-plugin"]}))
        adapter = OpenCodeAdapter(self.ctx)
        with quiet():
            report = adapter.install()
        self.assertEqual(report.errors, [])
        data = json.loads((self.cfg / "opencode.json").read_text())
        self.assertEqual(data["plugin"], ["my-plugin"])
        self.assertIn(f"{REPO}/AGENTS.md", data["instructions"])
        for link, src in (("agent", "agents"), ("command", "commands"), ("skill", "skills")):
            self.assertEqual((self.cfg / link).resolve(), (REPO / src).resolve())

        with quiet():
            again = adapter.install()
        self.assertEqual(again.created, [])
        self.assertEqual(again.backups, [])

        with quiet():
            adapter.uninstall()
            adapter.uninstall()
        self.assertEqual(sorted(p.name for p in self.cfg.iterdir()
                                if not p.name.startswith("opencode.json.bak")), ["opencode.json"])

    def test_refuses_to_replace_real_dir_without_force(self):
        (self.cfg / "agent").mkdir()
        (self.cfg / "agent" / "mine.md").write_text("x")
        with quiet():
            OpenCodeAdapter(self.ctx).install()
        self.assertTrue((self.cfg / "agent" / "mine.md").exists())
        self.assertFalse((self.cfg / "agent").is_symlink())

    def test_dry_run_writes_nothing(self):
        ctx = Context(repo_root=REPO, env={"BASE_PROJECT_PATH": str(REPO)}, dry_run=True,
                      overrides={"opencode_dir": str(self.cfg)})
        with quiet():
            OpenCodeAdapter(ctx).install()
        self.assertEqual(list(self.cfg.iterdir()), [])


class FakeClaudeCli:
    """Stands in for `claude mcp`: records calls and edits the user state file."""

    def __init__(self, state: Path):
        self.state = state
        self.calls = []

    def __call__(self, cmd, **kwargs):
        self.calls.append(cmd[2:])
        data = json.loads(self.state.read_text()) if self.state.exists() else {}
        servers = data.setdefault("mcpServers", {})
        if cmd[2] == "add-json":
            servers[cmd[5]] = json.loads(cmd[6])
        elif cmd[2] == "remove":
            servers.pop(cmd[-1], None)
        self.state.write_text(json.dumps(data))
        return subprocess.CompletedProcess(cmd, 0, "", "")


class ClaudeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.cfg = Path(tempfile.mkdtemp())
        self.ctx = Context(repo_root=REPO, env={"BASE_PROJECT_PATH": str(REPO)},
                           overrides={"claude_dir": str(self.cfg)})
        self.cli = FakeClaudeCli(self.cfg / ".claude.json")

    def tearDown(self):
        shutil.rmtree(self.cfg)

    def adapter(self, ctx=None, which=lambda cmd: "/usr/bin/" + cmd):
        a = ClaudeAdapter(ctx or self.ctx, runner=self.cli)
        a.which = which
        return a

    def test_registered(self):
        self.assertIs(ADAPTERS["claude"], ClaudeAdapter)

    def test_render_agent_and_command_frontmatter(self):
        cat = load_catalog(REPO, "global")
        agent = next(i for i in cat.agents if i.name == "code-reviewer")
        agent.meta["targets"] = {"claude": {"tools": ["Read", "Grep"], "model": "sonnet"}}
        meta, body = parse_frontmatter(render_item(agent))
        self.assertEqual(meta["name"], "code-reviewer")
        self.assertEqual(meta["tools"], "Read, Grep")
        self.assertEqual(meta["model"], "sonnet")
        self.assertNotIn("kind", meta)
        self.assertEqual(body.strip(), agent.body.strip())

        cmd = next(i for i in cat.commands if i.name == "review")
        meta, _ = parse_frontmatter(render_item(cmd))
        self.assertEqual(set(meta), {"description", "argument-hint"})

    def test_upsert_block_keeps_user_text(self):
        once = upsert_block("# mine\n", "<!-- ai-config:begin x -->\n@a\n<!-- ai-config:end -->\n")
        twice = upsert_block(once, "<!-- ai-config:begin x -->\n@b\n<!-- ai-config:end -->\n")
        self.assertTrue(twice.startswith("# mine\n"))
        self.assertIn("@b", twice)
        self.assertNotIn("@a", twice)

    def test_install_idempotent_then_uninstall(self):
        (self.cfg / "CLAUDE.md").write_text("# my notes\n")
        (self.cfg / "agents").mkdir()
        (self.cfg / "agents" / "mine.md").write_text("x")
        (self.cfg / "skills" / "synced").mkdir(parents=True)
        adapter = self.adapter()
        with quiet():
            report = adapter.install()
        self.assertEqual(report.errors, [])
        claude_md = (self.cfg / "CLAUDE.md").read_text()
        self.assertTrue(claude_md.startswith("# my notes"))
        self.assertIn(f"@{REPO}/AGENTS.md", claude_md)
        link = self.cfg / "agents" / "code-reviewer.md"
        self.assertTrue(link.is_symlink())
        self.assertIn('name: "code-reviewer"', link.read_text())
        self.assertTrue((self.cfg / "commands" / "review.md").is_symlink())
        self.assertEqual((self.cfg / "skills" / "csv-ledger").resolve(), REPO / "skills" / "csv-ledger")
        servers = json.loads((self.cfg / ".claude.json").read_text())["mcpServers"]
        self.assertEqual(servers["memory"]["env"]["MEMORY_FILE_PATH"],
                         str(Path.home() / ".local/share/ai-config/memory/store.json"))
        self.assertNotIn("~", " ".join(servers["filesystem"]["args"]))

        calls = len(self.cli.calls)
        with quiet():
            again = adapter.install()
        self.assertEqual(again.created, [])
        self.assertEqual(len(self.cli.calls), calls)

        with quiet():
            adapter.uninstall()
            adapter.uninstall()
        self.assertEqual((self.cfg / "CLAUDE.md").read_text(), "# my notes\n")
        self.assertEqual([p.name for p in (self.cfg / "agents").iterdir()], ["mine.md"])
        self.assertEqual([p.name for p in (self.cfg / "skills").iterdir()], ["synced"])
        self.assertEqual(json.loads((self.cfg / ".claude.json").read_text())["mcpServers"], {})

    def test_mcp_keeps_user_server_unless_forced(self):
        (self.cfg / ".claude.json").write_text(json.dumps(
            {"mcpServers": {"git": {"type": "stdio", "command": "my-git"}}}))
        with quiet():
            report = self.adapter().install()
        self.assertTrue(any("mcp git" in c for c in report.collisions))
        servers = json.loads((self.cfg / ".claude.json").read_text())["mcpServers"]
        self.assertEqual(servers["git"]["command"], "my-git")

        with quiet():
            self.adapter().uninstall()
        servers = json.loads((self.cfg / ".claude.json").read_text())["mcpServers"]
        self.assertEqual(servers, {"git": {"type": "stdio", "command": "my-git"}})

        forced = Context(repo_root=REPO, env=self.ctx.env, force=True, overrides=self.ctx.overrides)
        with quiet():
            self.adapter(forced).install()
        servers = json.loads((self.cfg / ".claude.json").read_text())["mcpServers"]
        self.assertEqual(servers["git"]["command"], "uvx")

    def test_mcp_skips_missing_command(self):
        with quiet():
            report = self.adapter(which=lambda cmd: None if cmd == "uvx" else "/x").install()
        servers = json.loads((self.cfg / ".claude.json").read_text())["mcpServers"]
        self.assertNotIn("git", servers)
        self.assertIn("memory", servers)
        self.assertTrue(any("`uvx` not found" in n for n in report.notes))

    def test_dry_run_writes_nothing(self):
        dry = Context(repo_root=REPO, env=self.ctx.env, dry_run=True, overrides=self.ctx.overrides)
        with quiet():
            report = self.adapter(dry).install()
        self.assertTrue(report.created)
        self.assertEqual(list(self.cfg.iterdir()), [])
        self.assertEqual(self.cli.calls, [])


    def test_frontmatter_is_valid_yaml(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        cat = load_catalog(REPO, "global")
        agent = next(i for i in cat.agents if i.name == "code-reviewer")
        agent.meta["targets"] = {"claude": {"tools": ["*"], "model": "@x # y",
                                            "hooks": {"Stop": [{"cmd": "a"}]}}}
        rendered = render_item(agent)
        self.assertEqual(parse_frontmatter(rendered)[0]["hooks"], {"Stop": [{"cmd": "a"}]})
        meta = yaml.safe_load(rendered.split("---")[1])
        self.assertEqual(meta["tools"], "*")
        self.assertEqual(meta["model"], "@x # y")
        self.assertEqual(meta["hooks"], {"Stop": [{"cmd": "a"}]})
        for item in cat.agents + cat.commands:
            yaml.safe_load(render_item(item).split("---")[1])

    def test_user_symlink_is_never_replaced_without_force(self):
        mine = self.cfg / "dotfiles-review.md"
        mine.write_text("my review")
        (self.cfg / "commands").mkdir()
        link = self.cfg / "commands" / "review.md"
        link.symlink_to(mine)
        with quiet():
            report = self.adapter().install()
        self.assertEqual(Path(os.readlink(link)), mine)
        self.assertTrue(any("review.md" in c for c in report.collisions))
        with quiet():
            self.adapter().uninstall()
        self.assertEqual(Path(os.readlink(link)), mine)

        forced = Context(repo_root=REPO, env=self.ctx.env, force=True, overrides=self.ctx.overrides)
        with quiet():
            report = self.adapter(forced).install()
        self.assertIn(str(REPO), os.path.realpath(link))
        backups = list((self.cfg / "commands").glob("review.md.bak.*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(Path(os.readlink(backups[0])), mine)

    def test_symlinked_claude_md_is_written_through(self):
        real = self.cfg / "dotfiles-CLAUDE.md"
        real.write_text("# dotfiles\n")
        (self.cfg / "CLAUDE.md").symlink_to(real)
        with quiet():
            self.adapter().install()
        self.assertTrue((self.cfg / "CLAUDE.md").is_symlink())
        self.assertIn("@", real.read_text())
        with quiet():
            self.adapter().uninstall()
        self.assertTrue((self.cfg / "CLAUDE.md").is_symlink())
        self.assertEqual(real.read_text(), "# dotfiles\n")

    def test_broken_markers_leave_file_alone(self):
        text = "<!-- ai-config:begin x -->\n# my notes, end marker deleted\n"
        (self.cfg / "CLAUDE.md").write_text(text)
        with self.assertRaises(BrokenBlock):
            upsert_block(text, "<!-- ai-config:begin y -->\n@a\n<!-- ai-config:end -->\n")
        with quiet():
            report = self.adapter().install()
            self.adapter().install()
            self.adapter().uninstall()
        self.assertTrue(any("markers" in c for c in report.collisions))
        self.assertEqual((self.cfg / "CLAUDE.md").read_text(), text)

    def test_block_only_file_is_removed_on_uninstall(self):
        with quiet():
            self.adapter().install()
            self.adapter().uninstall()
        self.assertFalse((self.cfg / "CLAUDE.md").exists())
        self.assertEqual(list(self.cfg.glob("CLAUDE.md.bak.*")), [])

    def test_local_layer_install_and_uninstall(self):
        repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, repo)
        shutil.copytree(REPO / "ai", repo / "ai")
        ctx = Context(repo_root=repo, env={"BASE_PROJECT_PATH": str(repo)})
        adapter = self.adapter(ctx)
        with quiet():
            report = adapter.install_local()
        self.assertEqual(report.errors, [])
        local = repo / ".claude"
        self.assertTrue((local / "agents" / "setup-doctor.md").is_file())
        self.assertTrue((local / "commands" / "sync.md").is_file())
        self.assertTrue((local / "skills" / "setup-doctor" / "SKILL.md").is_file())
        self.assertIn("@../ai/AGENTS.md", (local / "CLAUDE.md").read_text())
        with quiet():
            adapter.uninstall_local()
        self.assertEqual(list(local.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
