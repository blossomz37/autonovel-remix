---
file: CHANGELOG.md
description: Log of notable changes and refactoring efforts across the autonovel-remix pipeline.
version: 2.0.0
created: 2026-05-31
modified: 2026-05-31
author: Carlo
---

# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] — feature/openrouter-sdk

### Added

- **OpenRouter SDK integration**: Replaced raw `httpx` calls with the OpenAI SDK pointed at OpenRouter, introducing streaming support, structured reasoning configs, and per-call token/cost logging via a centralized `api_client.py` module.
- **Reasoning & verbosity controls**: New `.env` variables (`OPENROUTER_REASONING_EFFORT`, `OPENROUTER_REASONING_MAX_TOKENS`, `OPENROUTER_REASONING_EXCLUDE`, `OPENROUTER_REASONING_ENABLED`, `OPENROUTER_VERBOSITY`) for fine-grained control over model reasoning behavior.
- **Template system**: Created `templates/` directory with blank starter files (`seed-template.txt`, `world-template.md`, `characters-template.md`, `canon-template.md`, `outline-template.md`, `voice-template.md`, `genre-template.md`) so the pipeline can bootstrap a fresh novel without leftover lore.
- **Genre flexibility**: Renamed `MYSTERY.md` to `genre.md` and added a `genre-template.md`, decoupling the pipeline from any single genre.
- **Auto-select flag**: `seed.py` gained a `--auto-select` flag for fully autonomous seed selection during unattended runs.
- **Live progress dashboard** (`scripts/dashboard.py` + `auto-novel-progress.html`):
  - Three-panel IDE-style layout (file tree, markdown preview, inspector) with glassmorphism styling and rainbow colour scheme.
  - Live markdown rendering with tabbed file preview.
  - Resizable inspector panel showing `state.json`, `results.tsv`, and evaluation logs as collapsible sections.
  - Word counts in the sidebar file tree, file-type icons, auto-expand chapters, and scroll-to-top on file switch.
  - `SO_REUSEADDR` to prevent port-in-use crashes on restart.
- **Workspace isolation**: Novel output (chapters, lore, briefs, eval logs, data, manuscript) now lives under `workspace/`, keeping the repo root clean across runs.
- **Test fixtures**: Added `tests/v1-test/` (legacy lore snapshot) and `tests/v2-test/` (3-chapter mini-run with usage data) for regression testing.
- **Export artifacts**: `workspace/manuscript.md` (combined novel), compiled outline, arc summaries, and PDF export.
- **`reviews.md`**: Aggregated human review notes from revision rounds.

### Changed

- **Config universalisation**: Removed all hardcoded novel-specific references ("Cass", "House of Bells", "fantasy") from every `.toml` config file, making the pipeline genre- and story-agnostic.
- **Script API migration**: All 27 scripts in `scripts/` updated to call `api_client.py` instead of raw HTTP, gaining automatic retry, streaming, and cost tracking for free.
- **README overhaul**: Full rewrite documenting the autonovel-remix architecture, OpenRouter model examples (updated for 2026 availability), and the new directory layout.
- **Documentation cleanup**: Removed noise lines (system-generated edits, grep results, file views) from exported chat logs in `docs/chats/`.
- **Removed deprecated code**: Deleted `scripts/refactor_api_calls.py` (one-time migration script, no longer needed).

### Pipeline Run (Cozy Horror — 12 chapters)

- **Foundation**: Achieved score 8.0 (lore 9.0) on iteration 1 after initial calibration runs.
- **Drafting**: 12 chapters drafted, scores ranging 6.7–8.0, total ~27k words.
- **Revision**: 3 automated revision cycles followed by 4 manual review rounds (ch06 focus), including mechanical cleanup passes.
- **Final state**: `phase: complete`, 24 chapters capacity, 12 drafted, 3 revision cycles, exported manuscript.

### Security

- **SAST remediation (shell injection)**: Removed `shell=True` from `subprocess.run` calls in `run_pipeline.py` and `run_drafts.py`. Replaced with `shlex.split` tokenisation and native Python I/O for shell operators.

---

## [1.0.0] — 2026-05-31 (Initial Commit)

### Added

- Full autonovel pipeline: 27 Python scripts covering seed generation, world-building, character creation, outlining, drafting, revision, adversarial editing, reader panels, art generation, and audiobook scripting.
- TOML-based configuration in `config/` for all model hyperparameters and system prompts.
- Framework documentation (`framework/`): `CRAFT.md`, `ANTI-SLOP.md`, `ANTI-PATTERNS.md`, `PIPELINE.md`, `WORKFLOW.md`, `SCRIPT_ARCHITECTURE.md`.
- Lore directory (`lore/`) for per-novel context files.
- `.gitignore` covering macOS/Windows/Linux system files, Python build artefacts, `.gemini/`, and `workspace_antigravity/`.
- `AGENTS.md` orientation guide for AI agents operating in the workspace.
