---
type: command
trigger: "/pimp-readme"
---

# /pimp-readme

## Purpose

Analyze the current project's README.md and propose an improved version that's more polished, welcoming, and GitHub-ready — with a light touch of emoji, sensible badges, installation instructions, and a clear structure.

## Usage

```
/pimp-readme [--write]
```

## Parameters

- `--write` — optional; write the improved README directly to `README.md` (the original is overwritten).

## Behavior

1. **Discover** — reads the existing `README.md` in the project root. If none exists, reports that and offers to create one from scratch.
2. **Audit** — analyzes the current README for:
   - Missing sections (description, installation, usage, contributing, license)
   - Weak or missing title
   - No badges (checks if CI config, package.json, etc. exist to infer relevant badges)
   - Tone (too dry, too verbose, unclear audience)
   - Broken or missing structure (no TOC, no headings, wall of text)
3. **Enrich** — cross-references project files to suggest contextual badges:
   - CI status (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`)
   - Package version (`package.json`, `Cargo.toml`, `pyproject.toml`, `Gemfile`)
   - License (checks for `LICENSE`, `LICENSE.md`, `LICENSE.txt`)
   - Language/tech stack from project config files
4. **Draft** — proposes an improved README with:
   - A welcoming, friendly-but-technical tone
   - Up to **5 emojis** total (used meaningfully, never gratuitous)
   - **Installation instructions** (always included, inferred from project config)
   - A clear structure (badges → description → TOC → installation → usage → contributing → license)
   - The license section references the actual license file if present
5. **Deliver** — prints the proposed README as a diff or full preview. Unless `--write` is passed, does not touch the filesystem.

## Constraints

- **`--write` overwrites `README.md` in-place.** No backup is created — commit first or use version control to revert.
- **Maximum 5 emojis** in the entire document. Each must serve a purpose (section header, value prop, or callout).
- **Installation instructions are mandatory.** If the project's install method can't be inferred, prompt the user.
- **License section must match reality.** If a license file exists, link to it and state the type. If none exists, suggest adding one — do not invent a license.
- **Badges must be real.** Only suggest badges that can actually be resolved (infer from files present). Do not add placeholder badge URLs.
- **Preserve existing technical content.** Improve structure and tone, but keep all technical details, API docs, and configuration examples intact unless they're outdated.

## Examples

### Example 1 — Basic project with a sparse README

**Input:** `/pimp-readme`

**Output:**
```
📄 README Audit
   ✔ Project description: missing
   ✔ Installation: missing
   ✔ Badges: none (but package.json found)
   ✔ License: MIT (LICENSE file found)
   ✔ Structure: flat, no headings

✨ Proposed improvements:
   - Add a descriptive project title and tagline
   - Add CI + version badges
   - Add table of contents
   - Add installation section (npm install)
   - Add contributing guidelines (link to CONTRIBUTING.md)
   - Add license section (MIT)
   - Improve tone: friendly + technical

View the full proposal with /pimp-readme --write
```

### Example 2 — Comprehensive README, minor polish

**Input:** `/pimp-readme`

**Output:**
```
📄 README Audit
   ✔ Project description: present
   ✔ Installation: present (pip install)
   ✔ Badges: present (CI, Python version)
   ✔ License: present (Apache 2.0)
   ✔ Structure: well-organized

✨ Suggested tweaks:
   - Condense the "Getting Started" section
   - Move badges above the description
   - Add a "Contributing" section linking to the existing CONTRIBUTING.md
   - Minor tone polish (1-2 sentences feel too formal)

No major issues found. Run /pimp-readme --write to apply suggestions.
```

## See also

- `@docs-writer` agent for ADRs, docstrings, and full documentation projects.
- `@code-reviewer` agent for code correctness reviews.
