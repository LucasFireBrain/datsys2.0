import os
import json
import datetime
import shutil
import subprocess

# ============================================================
# CONFIG
# ============================================================

CONFIG_FILE   = "config.json"
CLIENTS_FILE  = "clients.json"
PROJECTS_FILE = "projects.json"
TEMPLATES_DIR = "templates"

PEEK_CASE_FILE = "peekCase.json"
HOSPITALS_FILE = "hospitals.json"

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DATE_FMT_INTERNAL = "%Y-%m-%d"

try:
    from peek_workflow.peek_workflow import (
        run_peek_initialization,
        import_dicom_into_project
    )
except ImportError:
    def run_peek_initialization(*a, **k):
        print("[i] PEEK workflow not available.")
    def import_dicom_into_project(*a, **k):
        print("[i] DICOM import not available.")
        return {"ok": False}

# ============================================================
# BASIC HELPERS
# ============================================================

def ensure_dir(p): os.makedirs(p, exist_ok=True)
def iso_now(): return datetime.datetime.now().isoformat()
def now_stamp(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def save_json(p, d):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def load_json(p, default):
    if not os.path.exists(p):
        save_json(p, default)
        return default
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def open_default(path):
    if os.name == "nt":
        os.startfile(path)

# ============================================================
# DATE / ID
# ============================================================

def to_base36(n): return DIGITS[n]

def today_date_code():
    now = datetime.datetime.now()
    return f"{to_base36(now.year % 100)}{to_base36(now.month)}{now.day:02d}"

def make_project_id(client_id, existing, type_code):
    prefix = f"{today_date_code()}-{client_id}-{type_code}"
    count = sum(1 for p in existing if p.startswith(prefix))
    return f"{prefix}{count + 1}"

# ============================================================
# LOG.txt
# ============================================================

def ensure_log(project_path):
    p = os.path.join(project_path, "LOG.txt")
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write("LOG.txt\n\n")
    return p

def append_event(project_path, event, msg, user=""):
    line = f"{now_stamp()} | {event} | {msg}"
    if user:
        line += f" | by {user}"
    with open(ensure_log(project_path), "a", encoding="utf-8") as f:
        f.write(line + "\n")

def tail_log(project_path, n=4):
    p = os.path.join(project_path, "LOG.txt")
    if not os.path.exists(p): return []
    with open(p, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if "|" in l][-n:]

# ============================================================
# INIT ENV / INDEX
# ============================================================

def init_env():
    ensure_dir(TEMPLATES_DIR)
    for f, d in [
        (CONFIG_FILE, {"root_path": "", "current_user": "", "blender_exe": ""}),
        (CLIENTS_FILE, {}),
        (PROJECTS_FILE, {}),
    ]:
        if not os.path.exists(f):
            save_json(f, d)

def rebuild_index(root, clients, projects):
    if not root: return
    for cid in os.listdir(root):
        cdir = os.path.join(root, cid)
        if not os.path.isdir(cdir): continue
        clients.setdefault(cid, {"id": cid, "projects": []})
        for pid in os.listdir(cdir):
            pdir = os.path.join(cdir, pid)
            if not os.path.isdir(pdir): continue
            projects.setdefault(pid, {
                "id": pid,
                "client_id": cid,
                "path": pdir,
                "created_at": iso_now(),
                "last_opened": iso_now(),
            })
            if pid not in clients[cid]["projects"]:
                clients[cid]["projects"].append(pid)

    save_json(CLIENTS_FILE, clients)
    save_json(PROJECTS_FILE, projects)

# ============================================================
# BLENDER INIT (RESTORED)
# ============================================================

def init_blender_project(project, config):
    blender = config.get("blender_exe")
    if not blender or not os.path.exists(blender):
        print("[!] Blender path not configured")
        return

    blend_dir = os.path.join(project["path"], "Blender")
    seg_dir   = os.path.join(project["path"], "3DSlicer", "Segmentations")

    blends = [f for f in os.listdir(blend_dir) if f.endswith(".blend")]
    if not blends:
        print("[!] No .blend file found")
        return

    cmd = [
        blender,
        os.path.join(blend_dir, blends[0]),
        "--python",
        "init_blender_project.py",
        "--",
        seg_dir
    ]

    subprocess.Popen(cmd)
    print("[✓] Blender launched")

# ============================================================
# DASHBOARD
# ============================================================

def dashboard(config, projects, pid):
    proj = projects[pid]
    path = proj["path"]
    ensure_log(path)

    while True:
        meta = load_json(os.path.join(path, f"{pid}.json"), {})
        notes = tail_log(path)

        print("\n==============================")
        print(f"Project: {pid}")
        print(f"Client: {proj['client_id']}")
        print(f"Status: {meta.get('status','')}")
        print("\nRecent notes:")
        for n in notes: print(f"- {n}")

        print("\nOptions:")
        print("1. Open project in Explorer")
        print("2. Export project report")
        print("3. Update project status")
        print("4. Open LOG.txt")
        print("5. PEEK Case Info")
        print("6. Import DICOM")
        print("7. Init Blender project")
        print("[B] Back")

        c = input("> ").strip().lower()

        if c == "1": open_default(path)

        elif c == "3":
            new = input("New status: ").strip()
            if new:
                meta["status"] = new
                meta["last_updated"] = iso_now()
                save_json(os.path.join(path, f"{pid}.json"), meta)
                append_event(path, "STATUS", new, config["current_user"])

        elif c == "4": open_default(os.path.join(path, "LOG.txt"))

        elif c == "6":
            r = import_dicom_into_project(path)
            if r.get("ok"):
                append_event(path, "DICOM", f"Imported to {r.get('dest')}", config["current_user"])

        elif c == "7":
            init_blender_project(proj, config)

        elif c == "b": break

# ============================================================
# MAIN
# ============================================================

def main():
    init_env()
    config = load_json(CONFIG_FILE, {})
    clients = load_json(CLIENTS_FILE, {})
    projects = load_json(PROJECTS_FILE, {})

    if not config.get("current_user"):
        config["current_user"] = input("Username: ").strip()
        save_json(CONFIG_FILE, config)

    if not config.get("root_path"):
        config["root_path"] = input("Root path: ").strip()
        save_json(CONFIG_FILE, config)

    rebuild_index(config["root_path"], clients, projects)

    while True:
        print("\n=== DATSYS ===")
        print("1. New Project")
        print("2. Open Project")
        print("3. Exit")
        c = input("> ").strip()

        if c == "2":
            pid = list(projects.keys())[0] if projects else None
            if pid:
                dashboard(config, projects, pid)
        elif c == "3":
            break

if __name__ == "__main__":
    main()
