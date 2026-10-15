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
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from installer import migrations  # noqa: E402
from installer.adapters import ADAPTERS  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
