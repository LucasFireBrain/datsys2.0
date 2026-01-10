# DATSYS

**DATSYS** is a filesystem-first, CLI-driven project management system designed for medical 3D workflows, with a strong focus on **PEEK implant cases**.

This repository represents **DATSYS 2.0**, uploaded as a reference point for review before designing **DATSYS 3.0** from scratch.

The goal of DATSYS is not to replace existing tools, but to **orchestrate them deterministically**, keeping the filesystem as the single source of truth.

---

## Core Principles

- **Filesystem is truth**
  - Folders and files define reality.
  - JSON files describe metadata, never replace structure.

- **Deterministic workflows**
  - Same input → same result.
  - Scripts are idempotent and predictable.

- **Separation of concerns**
  - DATSYS launches and navigates.
  - Workflows do the real work.
  - No script owns more than one domain.

- **Minimal UI**
  - CLI-first.
  - Fast keyboard-driven flow.
  - No hidden state.

---

## Current State (DATSYS 2.0)

DATSYS 2.0 includes:

- `datsys.py`
  - CLI entry point
  - Project creation
  - Project navigation
  - Logging
  - Partial workflow invocation

- `peek_workflow/`
  - PEEK-specific initialization
  - DICOM import helpers
  - Slicer automation scripts
  - Hospital manager utilities

- Templates system
  - Project skeletons
  - `peekCase.json` for PEEK cases
  - Base directory layouts

This version **works**, but has accumulated complexity and responsibility bleed over time.

---

## Known Limitations of 2.0

This repository is intentionally frozen in its current state to allow a clean redesign.

Main issues identified:

- Responsibility creep in `datsys.py`
- Multiple overlapping sources of truth
- Workflow logic partially embedded in the launcher
- Menu options tied to mutable state
- Increasing fragility during refactors

These are **architectural**, not implementation, problems.

---

## Vision for DATSYS 3.0

DATSYS 3.0 will be a **clean rewrite**, not an iteration.

High-level goals:

- DATSYS becomes a **launcher**, not a brain
- Clients and projects discovered from folders, not indexes
- Each workflow lives in its own isolated script
- Zero hidden state
- Explicit, documented contracts between components

No code from 2.0 will be blindly reused.

---

## Repository Purpose

This repo exists to:

- Preserve working ideas
- Document mistakes
- Serve as a reference during redesign
- Avoid repeating architectural errors

It is **not** the future production version.

---

## Status

- 🧊 Frozen
- 🔍 Under review
- ✏️ Documentation-first redesign in progress

---

## Author

Built and maintained by **Lucas** as part of an evolving medical 3D production system.

