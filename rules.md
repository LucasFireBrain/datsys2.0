# DATSYS 3.0 – Locked Menu Flow & Guarantees

## 1. Locked CLI Menu Flow (Text-Only)

### Main Menu
```
=== DATSYS 3.0 ===
1. New project
2. Open project
3. Exit
>
```

---

### New Project Flow
```
> 1

Enter client ID:
> PSO

Client found:
ID: PSO
Name: Pablo Solé

Confirm client? [Y/n]:
> Y

Select project type:
1. PK (PEEK)
2. PL
3. AR
4. X
>
```

```
> 1

Suggested Project ID:
Q109-PSO-PK5

Press ENTER to confirm or type a new ID:
>
```

```
Project created.
Opening project: Q109-PSO-PK5
```

→ Lands in **Project Menu**

---

### Open Project Flow
```
> 2

Filter by project ID (ENTER = recent):
>
```

```
1. Q109-PSO-PK5
2. Q108-PSO-PK4
>
```

```
> 1

Opening project: Q109-PSO-PK5
```

→ Lands in **Project Menu**

---

### Project Menu (Generic)
```
=== Project: Q109-PSO-PK5 ===
Client: PSO

1. Open project folder
2. Open project.blend
3. Export report
4. Open LOG.txt
5. Project-specific tools
[B] Back
>
```

---

### Project-Specific Tools (PK Only)
```
=== PEEK Tools ===
1. Edit PEEK case info
2. Import DICOM and open Slicer
3. Init Blender project (import segmentations)
[B] Back
>
```

---

## 2. Hard Guarantees (Non-Negotiable Rules)

1. **DATSYS never edits files outside a project folder**
   Global files are read-only indexes or configs.

2. **The project folder is the source of truth**
   If a file exists in the folder, DATSYS adapts to it — never the other way around.

3. **Workflows are explicit**
   Nothing happens automatically unless the user selects it in the menu.

4. **No hidden side effects**
   No background edits, no silent imports, no implicit state changes.

5. **Menus do not change dynamically**
   Options never disappear based on partial state — they may show warnings instead.

6. **One responsibility per script**
   - datsys.py → navigation & orchestration
   - workflows/* → domain actions only
   - utils/* → pure helpers

7. **If it breaks, it fails loud**
   Errors are printed clearly. No silent fallbacks.

---

This document is binding for DATSYS 3.0.
