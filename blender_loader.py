# blender_loader.py

import os
import subprocess

BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"

SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "blender_scripts",
    "init_blender_project.py"
)

def launch_blender_with_segmentations(project_path: str, project_id: str):
    blend_file = os.path.join(project_path, "Blender", f"{project_id}.blend")
    seg_dir = os.path.join(project_path, "3DSlicer", "Segmentations")

    if not os.path.isfile(BLENDER_EXE):
        print("[!] Blender not found.")
        return

    if not os.path.isfile(blend_file):
        print("[!] Blend file not found:", blend_file)
        return

    if not os.path.isdir(seg_dir):
        print("[!] Segmentations folder not found:", seg_dir)
        return

    cmd = [
        BLENDER_EXE,
        blend_file,
        "--python",
        SCRIPT_PATH,
        "--",
        seg_dir
    ]

    print("[BLENDER] Launching Blender with segmentations loaded…")
    subprocess.Popen(cmd)
