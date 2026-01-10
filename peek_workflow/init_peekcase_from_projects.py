import os
import json
import re
import argparse
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

ROOT = r"C:\Users\Lucas\Desktop\Hexamod\Clients\Hexamod\Datsys\clients"
PEEK_CASE_FILE = "peekCase.json"
CLIENTS_FILE = "clients.json"

# Matches:
# PC18-AFU-PK1
# PB13-LPZ-PK02
# PC03-PSO-PK3
CASE_REGEX = re.compile(r"^[A-Z0-9]+-[A-Z]{2,4}-PK\d{1,2}$")

# ============================================================
# HELPERS
# ============================================================

def iso_now():
    return datetime.now().isoformat()

def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def matches_peek_project(name: str) -> bool:
    return bool(CASE_REGEX.match(name))

def extract_doctor_id(project_dir: str) -> str:
    # PC18-AFU-PK1 → AFU
    try:
        return project_dir.split("-")[1]
    except Exception:
        return ""

# ============================================================
# CORE LOGIC
# ============================================================

def process_projects(root, apply=False):
    clients_db = load_json(CLIENTS_FILE, {}) or {}

    stats = {
        "create": [],
        "update": [],
        "skip": [],
    }

    for client_id in os.listdir(root):
        client_path = os.path.join(root, client_id)
        if not os.path.isdir(client_path):
            continue

        for project_dir in os.listdir(client_path):
            project_path = os.path.join(client_path, project_dir)
            if not os.path.isdir(project_path):
                continue

            # Only care about PEEK projects
            if not matches_peek_project(project_dir):
                continue

            peek_path = os.path.join(project_path, PEEK_CASE_FILE)
            doctor_id = extract_doctor_id(project_dir)
            doctor = clients_db.get(doctor_id, {})

            # ----------------------------
            # CREATE peekCase.json
            # ----------------------------
            if not os.path.exists(peek_path):
                stats["create"].append(project_path)

                if apply:
                    peek = {
                        "id_caso": project_dir,
                        "doctor_id": doctor_id,
                        "nombre_doctor": (
                            doctor.get("nombre")
                            or doctor.get("name")
                            or ""
                        ),
                        "hospital_clinica": "",
                        "nombre_paciente": "",
                        "fecha_cirugia": "",
                        "fecha_entrega_estimada": "",
                        "region": "",
                        "especificaciones": "",
                        "precio_clp": "",
                        "origen": "init_from_project_dir",
                        "creado_en": iso_now(),
                        "actualizado_en": iso_now(),
                    }
                    save_json(peek_path, peek)

            # ----------------------------
            # UPDATE id_caso only
            # ----------------------------
            else:
                peek = load_json(peek_path, {}) or {}
                if not peek.get("id_caso"):
                    stats["update"].append(project_path)

                    if apply:
                        peek["id_caso"] = project_dir
                        peek["actualizado_en"] = iso_now()
                        save_json(peek_path, peek)
                else:
                    stats["skip"].append(project_path)

    return stats

# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Initialize peekCase.json from clients/<CLIENT>/<PROJECT_DIR>"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (default: dry-run)"
    )
    args = parser.parse_args()

    stats = process_projects(ROOT, apply=args.apply)

    print("\n=== APPLY SUMMARY ===" if args.apply else "\n=== DRY RUN SUMMARY ===")
    print(f"CREATE: {len(stats['create'])}")
    print(f"UPDATE: {len(stats['update'])}")
    print(f"SKIP:   {len(stats['skip'])}")

    for key in ("create", "update"):
        if stats[key]:
            print(f"\n{key.upper()} examples:")
            for p in stats[key][:10]:
                print(" -", p)
            if len(stats[key]) > 10:
                print(f"   ... and {len(stats[key]) - 10} more")

    if not args.apply:
        print("\n[!] Dry run only. Re-run with --apply to write files.")

if __name__ == "__main__":
    main()
