"""Registry of coding-tool adapters. Add new tools here."""

from __future__ import annotations

from typing import Dict, Type

from .base import Adapter
from .opencode import OpenCodeAdapter

ADAPTERS: Dict[str, Type[Adapter]] = {
    OpenCodeAdapter.name: OpenCodeAdapter,
    # "pi": PiAdapter,          # Phase 4
    # "claude": ClaudeAdapter,  # Phase 4
}

__all__ = ["ADAPTERS", "Adapter"]
