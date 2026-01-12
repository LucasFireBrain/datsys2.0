# DATSYS 3.0 – Project Structure & Responsibilities

This document locks the **physical structure** of DATSYS 3.  
Structure comes **before** logic.  
If structure changes, rules must be revisited.

---

## Folder Structure

datsys3/
│
├─ datsys.py
│
├─ workflows/
│ └─ peek/
│ ├─ peek.py
│ ├─ dicom.py
│ ├─ blender.py
│ └─ init.py
│
├─ templates/
│ ├─ PK/
│ └─ BASE/
│
├─ data/
│ ├─ hospitals.json
│ └─ (future global reference data)
│
├─ docs/
│ ├─ scope.md
│ ├─ rules.md
│ └─ structure.md
│
└─ utils/
├─ fs.py
├─ dates.py
└─ init.py

yaml
Copy code

---

## File Responsibilities (Hard Rules)

### datsys.py
- Pure CLI router
- Shows menus
- Collects user input
- Calls workflows
- Knows **paths**, not file contents
- Never edits files directly (except project creation scaffolding)

---

### workflows/peek/peek.py
- Entry point for PEEK workflow
- Creates / loads `peekCase.json`
- Owns PEEK case state
- Calls `dicom.py` and `blender.py`
- Explicitly logs actions (no silent behavior)

---

### workflows/peek/dicom.py
- Handles DICOM import
- Launches Slicer
- May extract metadata (e.g. patient name)
- Never touches global state
- Operates only on provided project path

---

### workflows/peek/blender.py
- Launches Blender
- Imports segmentations
- Handles Blender-side automation
- Never scans outside project directory

---

### templates/
- Dumb data only
- Copied once at project creation
- Never modified in place
- No logic, no side effects

---

### data/
- Global reference data (hospitals, etc.)
- Read-only during workflows
- Edited only via explicit manager tools

---

### utils/
- Small pure helpers
- No side effects
- No workflow imports
- Safe to reuse everywhere

---

## Design Intent

- Predictability over cleverness
- One responsibility per file
- No hidden automation
- Easy deletion and rewrite of any workflow
- Bugs are local, not systemic

---

## Required First Commit

Create this structure with **empty files only**  
(no logic, no imports, `pass` allowed)

Commit message:

chore: datsys3 skeleton

arduino
Copy code

Only after this commit:
- write `datsys.py` router
- nothing else
