---
file: AGENTS.md
description: Orientation and rules for AI agents operating in this workspace.
version: 1.0.0
created: 2026-05-31
modified: 2026-05-31
author: Antigravity
---

# Agent Orientation Guide

Welcome! If you are an AI agent operating in this repository, please review and adhere to the following rules and orientation guidelines:

## Core Directives

1. **Workspace Outputs:** All agent-generated workspace outputs, artifacts, and scratch files must be directed to the `workspace_antigravity/` directory, **unless explicitly instructed otherwise** by the user. Do not pollute the root directory or other source directories with temporary files, scratch pads, or intermediate outputs.

2. **Shared Environment:** This is a shared workspace. Maintain a clean structure, and respect existing files and configurations.

3. **Global User Rules Apply:** Always refer to and adhere to the global user rules and any `.gemini/GEMINI.md` project-level overrides present on the system.

## Project Context
This is the `autonovel-master` repository, a pipeline for generating novels and audiobooks.
- Do not modify source code files destructively unless certain of the user's intent. 
- Follow existing patterns and consult `PIPELINE.md`, `WORKFLOW.md`, `CRAFT.md`, `ANTI-PATTERNS.md`, etc., for domain knowledge and constraints if needed.
