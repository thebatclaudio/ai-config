"""
ai-config installer: renders the tool-neutral sources of this repository into
each AI coding tool's native configuration. Entry point: ``setup.py``.

    core        shared helpers (env, templates, JSON merge, symlinks, recap)
    catalog     loads canonical agents/commands/skills/MCP (+ frontmatter parser)
    migrations  tool-neutral data housekeeping
    adapters/   one module per coding tool
"""
