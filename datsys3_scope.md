# DATSYS 3.0 — Scope & Responsibilities

## Purpose

DATSYS 3.0 is a **local, filesystem-driven project navigator and dispatcher**.

It exists to:
- Create projects
- Open projects
- Delegate work to specialized workflows (PEEK, etc.)
- Provide a stable, predictable interface over the filesystem

It does **not** try to be smart.
It does **not** manage medical logic.
It does **not** replace Blender, Slicer, or human judgment.

---

## Core Principle: Filesystem Is the Source of Truth

There is **no central database**.

Reality is defined by:
- Directories
- JSON files inside those directories
- Logs inside project folders

If a folder exists, the project exists.
If a file is missing, the system adapts or asks.

---

## What DATSYS 3.0 IS Responsible For

### 1. Project Creation
- Ask for **Client ID**
- If client folder exists:
  - Load `client.json`
  - Show client name
  - Ask for confirmation
- If client does not exist:
  - Create client folder
  - Create `client.json`

- Ask for **Project Type** (PK, PL, AR, etc.)
- Suggest Project ID using:
  ```
  <dateCode>-<clientID>-<TYPE><n>
  ```
- Confirm or allow override
- Create project folder
- Copy template
- Create minimal project metadata JSON
- Write initial LOG entry

---

### 2. Project Discovery & Navigation
- Scan client directories
- Scan project directories
- Never rely on cached indexes
- Never maintain parallel project lists

---

### 3. Project Dashboard
Once inside a project, DATSYS can:

- Open project folder
- Open main project file (e.g. `.blend`)
- Open LOG.txt
- Update project status
- Dispatch workflow-specific actions

DATSYS **does not** inspect geometry, DICOMs, or segmentations.

---

### 4. Workflow Delegation
DATSYS delegates actions to external scripts:
- `peek_workflow.py`
- future workflows

DATSYS:
- Passes explicit paths
- Receives structured results
- Logs meaningful events

DATSYS does **not** duplicate workflow logic.

---

### 5. Logging (Minimal & Honest)
DATSYS logs only:
- Project creation
- Status changes
- Workflow execution results (success / failure)

Logging is append-only.
Logs live **inside the project folder**.

---

## What DATSYS 3.0 Is NOT Responsible For

DATSYS must **never**:

- Parse DICOM metadata
- Touch Slicer’s internal database
- Decide which volume is correct
- Import meshes into Blender
- Perform segmentation
- Modify medical data
- Generate reports for HQ
- Maintain business rules
- Track commissions
- Act as a background service

If logic feels “smart”, it probably does not belong here.

---

## Workflow Responsibilities (Example: PEEK)

Each workflow:
- Is standalone
- Receives paths explicitly
- Operates only inside its project
- Owns its own logic

Example PEEK responsibilities:
- DICOM import
- Slicer launch
- Segmentation handling
- Patient metadata extraction
- Updating `peekCase.json`

DATSYS does **not** interpret PEEK data.

---

## Canonical Folder Structure

```
ROOT/
 └─ CLIENT_ID/
    ├─ client.json
    ├─ PROJECT_ID/
    │  ├─ PROJECT_ID.json
    │  ├─ peekCase.json (PK only)
    │  ├─ LOG.txt
    │  ├─ DICOM/
    │  ├─ Blender/
    │  ├─ 3DSlicer/
    │  └─ Misc/
```

---

## Menu Philosophy

Menus must be:
- Explicit
- Stable
- Predictable

Options must **never disappear silently**.
New options are added, not replaced.

---

## Design Constraints

- Single-file entry point (`datsys.py`)
- No global state beyond filesystem
- No magic paths
- No side effects without logging
- Easy to reason about after months away

---

## Success Criteria for DATSYS 3.0

DATSYS 3.0 is successful if:
- You can stop coding it
- It doesn’t break when workflows evolve
- You trust it during stressful cases
- It feels boring

Boring is correct.
