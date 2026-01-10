# slicer_loader.py
# Launch 3D Slicer and run open_dicom_in_slicer.py on a given DICOM folder.

import os
import subprocess

# Update this if your Slicer path changes
SLICER_EXE = r"C:\Users\Lucas\AppData\Local\slicer.org\Slicer 5.8.0\Slicer.exe"

def launch_slicer_with_dicom(dicom_folder: str, slicer_exe: str = SLICER_EXE) -> bool:
    dicom_folder = os.path.abspath(dicom_folder)

    if not os.path.isdir(dicom_folder):
        print(f"[!] DICOM folder not found: {dicom_folder}")
        return False

    if not os.path.isfile(slicer_exe):
        print(f"[!] Slicer.exe not found: {slicer_exe}")
        return False

    script_path = os.path.join(os.path.dirname(__file__), "open_dicom_in_slicer.py")
    if not os.path.isfile(script_path):
        print(f"[!] open_dicom_in_slicer.py not found next to slicer_loader.py: {script_path}")
        return False

    cmd = [
        slicer_exe,
        "--python-script", script_path,
        dicom_folder
    ]

    try:
        # non-blocking: you can keep using the terminal while Slicer loads
        subprocess.Popen(cmd, shell=False)
        print("[✓] Launched Slicer.")
        return True
    except Exception as e:
        print(f"[!] Failed to launch Slicer: {e}")
        return False
