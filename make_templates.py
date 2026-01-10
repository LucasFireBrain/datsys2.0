# make_templates.py
# Run once (safe to re-run). Creates a unified template structure.

import os

BASE = "templates"

FOLDERS = [
    "01_INBOX",
    "02_COMMS",
    "03_WORK",
    "04_EXPORTS",
    "05_ADMIN",
]

COMMON_FILES = {
    "LOG.txt": "LOG.txt\n\n",
    "PresetMessages.txt": (
        "PresetMessages.txt\n\n"
        "INTAKE (copy/paste):\n"
        "Hello, this is Lucas' virtual assistant.\n"
        "Please provide the following information:\n"
        "- Surgery Date:\n"
        "- Hospital:\n"
        "- Doctor in charge:\n"
        "- Patient name or identifier:\n"
    ),
}

# Job types -> which .blend placeholder file to include
TEMPLATES = {
    "BASE": ["Template.blend"],
    "PK":   ["PEEK.blend"],
    "PR":   ["3DPR.blend"],
    "DS":   ["DESIGN.blend"],
    "AD":   ["ADMIN.blend"],
    "RS":   ["RESEARCH.blend"],
}

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def ensure_file(path: str, content: str = ""):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

def main():
    ensure_dir(BASE)

    for tname, blend_files in TEMPLATES.items():
        tdir = os.path.join(BASE, tname)
        ensure_dir(tdir)

        # folders
        for f in FOLDERS:
            ensure_dir(os.path.join(tdir, f))

        # common files
        for fname, content in COMMON_FILES.items():
            ensure_file(os.path.join(tdir, fname), content)

        # .blend placeholders (empty files; replace with real .blend later)
        for b in blend_files:
            ensure_file(os.path.join(tdir, b), "")

    print("[✓] Templates created/verified:")
    for tname in TEMPLATES.keys():
        print(" -", os.path.join(BASE, tname))

if __name__ == "__main__":
    main()
