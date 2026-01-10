import os
import json
import re
import argparse
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

ROOT = r"C:\Users\Lucas\Desktop\Hexamod\Clients\Hexamod\Datsys\Clients"
PEEK_CASE_FILE = "peekCase.json"
CLIENTS_FILE = "clients.json"

CASE_REGEX = re.compile(r"^PC\d{2}-[A-Z]{2,4}-PK\d$")

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

def matches_case_name(name):
    return bool(CASE_REGEX.match(name))

def extract_doctor_id(case_id):
    # PC18-AFU-PK1 -> AFU
    try:
        return case_id.split("-")[1]
    except Exception:
        return ""

# ============================================================
# CORE LOGIC
# ============================================================

def process_directories(root, apply=False):
    clients_db = load_json(CLIENTS_FILE, {}) or {}

    stats = {
        "create": [],
        "update": [],
        "delete": [],
        "skip": [],
    }

    for dirpath, dirnames, filenames in os.walk(root):
        dirname = os.path.basename(dirpath)
        peek_path = os.path.join(dirpath, PEEK_CASE_FILE)

        is_case_dir = matches_case_name(dirname)
        has_peek = PEEK_CASE_FILE in filenames

        # ----------------------------
        # VALID CASE DIR
        # ----------------------------
        if is_case_dir:
            doctor_id = extract_doctor_id(dirname)
            doctor = clients_db.get(doctor_id, {})

            if not has_peek:
                stats["create"].append(dirpath)

                if apply:
                    peek = {
                        "id_caso": dirname,
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
                        "origen": "auto_init_by_name",
                        "creado_en": iso_now(),
                        "actualizado_en": iso_now(),
                    }
                    save_json(peek_path, peek)

            else:
                peek = load_json(peek_path, {})
                changed = False

                if not peek.get("id_caso"):
                    peek["id_caso"] = dirname
                    changed = True

                if changed:
                    stats["update"].append(dirpath)
                    if apply:
                        peek["actualizado_en"] = iso_now()
                        save_json(peek_path, peek)
                else:
                    stats["skip"].append(dirpath)

        # ----------------------------
        # INVALID DIR WITH peekCase.json
        # ----------------------------
        else:
            if has_peek:
                stats["delete"].append(dirpath)
                if apply:
                    os.remove(peek_path)

    return stats

# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Repair / normalize peekCase.json files")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    args = parser.parse_args()

    stats = process_directories(ROOT, apply=args.apply)

    print("\n=== DRY RUN SUMMARY ===" if not args.apply else "\n=== APPLY SUMMARY ===")

    for k in ["create", "update", "delete", "skip"]:
        print(f"{k.upper():>8}: {len(stats[k])}")

    # Show samples
    for k in ["create", "update", "delete"]:
        if stats[k]:
            print(f"\n{k.upper()} examples:")
            for p in stats[k][:10]:
                print(" -", p)
            if len(stats[k]) > 10:
                print(f"   ... and {len(stats[k]) - 10} more")

    if not args.apply:
        print("\n[!] This was a DRY RUN. Re-run with --apply to make changes.")

if __name__ == "__main__":
    main()
