"""
repo_indexer.py

Build a lightweight file/symbol index of a repository.
Used by agents like /explain and refactor-surgeon for navigation.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class Symbol:
    """Represents a code symbol (function, class, method, etc.)."""
    name: str
    kind: str  # "function", "class", "method", "constant", etc.
    file: Path
    line: int
    docstring: Optional[str] = None


class RepoIndexer:
    """Lightweight repository indexer."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.files: List[Path] = []
        self.symbols: List[Symbol] = []
        self._indexed = False

    def index(self, skip_dirs: Optional[Set[str]] = None) -> None:
        """
        Index the repository. Walk the tree and collect files and symbols.
        """
        if skip_dirs is None:
            skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}

        for root, dirs, files in os.walk(self.repo_root):
            # Prune skipped directories in-place
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            for fname in files:
                fpath = Path(root) / fname
                self.files.append(fpath)

                # Attempt to extract symbols (stub; real implementation parses code)
                if fname.endswith(".py"):
                    self._extract_python_symbols(fpath)

        self._indexed = True

    def _extract_python_symbols(self, path: Path) -> None:
        """Extract Python function/class definitions (stub)."""
        try:
            content = path.read_text(encoding="utf-8")
            for i, line in enumerate(content.split("\n"), 1):
                line = line.strip()
                if line.startswith("def "):
                    name = line.split("(")[0].replace("def ", "")
                    self.symbols.append(Symbol(name, "function", path, i))
                elif line.startswith("class "):
                    name = line.split("(")[0].split(":")[0].replace("class ", "")
                    self.symbols.append(Symbol(name, "class", path, i))
        except Exception:
            pass

    def find_symbol(self, name: str) -> Optional[Symbol]:
        """Find a symbol by name."""
        for sym in self.symbols:
            if sym.name == name:
                return sym
        return None

    def files_by_extension(self, ext: str) -> List[Path]:
        """Get all files with a specific extension."""
        return [f for f in self.files if f.suffix == ext]

    def file_count(self) -> int:
        """Total number of files indexed."""
        return len(self.files)

    def symbol_count(self) -> int:
        """Total number of symbols indexed."""
        return len(self.symbols)

    def stats(self) -> dict:
        """Return indexing statistics."""
        by_ext = {}
        for f in self.files:
            ext = f.suffix or "(no extension)"
            by_ext[ext] = by_ext.get(ext, 0) + 1

        by_kind = {}
        for sym in self.symbols:
            by_kind[sym.kind] = by_kind.get(sym.kind, 0) + 1

        return {
            "files_indexed": len(self.files),
            "symbols_indexed": len(self.symbols),
            "by_extension": by_ext,
            "by_kind": by_kind,
        }
