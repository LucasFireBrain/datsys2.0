import bpy
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

PEEK_MACROS_DIR = r"C:\Users\Lucas\Desktop\Hexamod\Clients\Hexamod\Datsys\PEEKMacros"

SCRIPTS = [
    "materialTools.py",
    "versionControl.py",
    "caseTools.py",
    "snapshotCameras.py",
    #keep others manual:
    #"autoFat.py",
    "decimateSelected.py",
    "quickBoolean.py",
    "idBridge.py",
    "islands.py",
    "minThickness"
]

# --------------------------------------------------

print("\n[DATSYS] Initializing PEEK macros...\n")

for script in SCRIPTS:
    path = os.path.join(PEEK_MACROS_DIR, script)

    if not os.path.isfile(path):
        print(f"[SKIP] {script} (not found)")
        continue

    print(f"[RUN ] {script}")

    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    exec(code, {"__name__": "__main__"})

print("\n[DATSYS] Macro initialization complete\n")
