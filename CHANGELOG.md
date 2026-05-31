---
file: CHANGELOG.md
description: Log of notable changes and refactoring efforts across the autonovel pipeline.
version: 1.0.0
created: 2026-05-31
modified: 2026-05-31
author: Antigravity
---

# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-05-31

### Added
- **`AGENTS.md`**: Added an orientation guide for AI agents operating in the workspace, ensuring output predictability and establishing global guidelines.
- **Gitignore Expansion**: Added comprehensive ignore rules for macOS, Linux, and Windows system files, as well as AI-specific `.gemini/` and `workspace_antigravity/` directories to prevent accidental commits.
- **Workspace Reports**: Generated structural security and SAST scan reports inside `workspace_antigravity/` to track codebase health and AI pipeline safety.

### Changed
- **Script Reorganization**: Moved all 27 Python scripts out of the root directory into a dedicated `scripts/` module. This massively cleans up the project root and isolates pipeline execution logic.
- **Data Reorganization**: Moved framework guidelines into a `framework/` directory and novel-specific context/lore files into a `lore/` directory.
- **Configuration Refactoring**: Extracted all hardcoded system prompts, user prompts, and model hyperparameters (like `temperature` and `max_tokens`) out of the python scripts. These are now defined in cleanly separated `.toml` files located within the new `config/` directory. Python scripts use the `tomllib` standard library to dynamically load these values.
- **Orchestration Execution Paths**: Updated `run_pipeline.py` and `run_drafts.py` to transparently route `uv run` commands into the new `scripts/` directory.
- **Relative Path Resolution**: Updated `BASE_DIR` logic in all scripts from `Path(__file__).parent` to `Path(__file__).parent.parent` so they correctly find artifacts in the root directory.
- **Documentation**: Updated the Quick Start examples in `README.md` to reflect the new `scripts/`, `lore/`, `framework/`, and `config/` folder routing.

### Security
- **SAST Remediation (Shell Injection Risk)**: Refactored `subprocess.run` executions across `run_pipeline.py` and `run_drafts.py`. Removed `shell=True` usages, implemented `shlex.split` for safe command tokenization, and replaced insecure shell pipeline logic (like `grep` and `wc -w`) with robust, native Python file I/O.
