# peek_workflow.py
# Minimal, deterministic PEEK workflow
# No logging, no user state, no duplication of DATSYS logic

import os
import shutil
import datetime
import zipfile

try:
    from slicer_loader import launch_slicer_with_dicom
except ImportError:
    def launch_slicer_with_dicom(path):
        print("[i] Slicer launcher not available.")

# ==================================================
# HELPERS
# ==================================================

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def now_stamp_fs() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def _copy_tree(src_dir: str, dest_dir: str) -> int:
    copied = 0
    for root, _, files in os.walk(src_dir):
        rel = os.path.relpath(root, src_dir)
        target_root = dest_dir if rel == "." else os.path.join(dest_dir, rel)
        ensure_dir(target_root)

        for fn in files:
            s = os.path.join(root, fn)
            d = os.path.join(target_root, fn)
            if not os.path.exists(d):
                shutil.copy2(s, d)
                copied += 1
    return copied

def _extract_zip(zip_path: str, dest_dir: str) -> int:
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest_dir)
        return len([m for m in z.namelist() if not m.endswith("/")])

def _rename_peek_blend(project_path: str, project_id: str):
    blender_dir = os.path.join(project_path, "Blender")
    src = os.path.join(blender_dir, "PEEK.blend")
    dst = os.path.join(blender_dir, f"{project_id}.blend")

    if os.path.exists(src) and not os.path.exists(dst):
        os.rename(src, dst)
        print(f"[✓] Renamed PEEK.blend → {project_id}.blend")

# ==================================================
# PEEK INITIALIZATION
# ==================================================

def run_peek_initialization(project_path: str, project_id: str):
    """
    Idempotent PEEK project setup.
    Assumes template already copied by DATSYS.
    """
    ensure_dir(os.path.join(project_path, "DICOM"))
    ensure_dir(os.path.join(project_path, "3DSlicer"))
    ensure_dir(os.path.join(project_path, "Blender"))
    ensure_dir(os.path.join(project_path, "Misc", "Reports"))
    ensure_dir(os.path.join(project_path, "Misc", "Comms"))
    ensure_dir(os.path.join(project_path, "Misc", "Refs"))

    _rename_peek_blend(project_path, project_id)

# ==================================================
# DICOM IMPORT
# ==================================================

def import_dicom_into_project(project_path: str, auto_open_slicer: bool = True) -> dict:
    """
    Imports DICOM into:
      <ProjectRoot>/DICOM/<timestamp>/

    Returns structured result for DATSYS logging.
    """
    raw = input("Enter DICOM folder OR .zip path: ").strip().strip('"')
    if not raw:
        return {"ok": False, "reason": "empty_path"}

    dest = os.path.join(project_path, "DICOM", now_stamp_fs())
    ensure_dir(dest)

    # ZIP import
    if os.path.isfile(raw) and raw.lower().endswith(".zip"):
        try:
            count = _extract_zip(raw, dest)

            if auto_open_slicer:
                launch_slicer_with_dicom(dest)

            return {
                "ok": True,
                "mode": "zip",
                "files": count,
                "dest": dest
            }

        except Exception as e:
            return {
                "ok": False,
                "reason": "zip_error",
                "error": str(e)
            }

    # Folder import
    if os.path.isdir(raw):
        count = _copy_tree(raw, dest)

        return {
            "ok": True,
            "mode": "folder",
            "files": count,
            "dest": dest
        }

    return {
        "ok": False,
        "reason": "invalid_path"
    }
