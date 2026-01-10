import os
import json
import csv
import datetime
import subprocess
import sys

# ============================================================
# CONFIG
# ============================================================

ROOT = r"C:\Users\Lucas\Desktop\Hexamod\Clients\Hexamod\Datsys\Clients"
PEEK_CASE_FILE = "peekCase.json"

CLIENTS_FILE   = "clients.json"
HOSPITALS_FILE = "hospitals.json"

DATE_FMT_INTERNAL = "%Y-%m-%d"
IVA = 1.19

# ============================================================
# BASIC HELPERS
# ============================================================

def load_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(p, d):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def iso_now():
    return datetime.datetime.now().isoformat()

def open_default(path):
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.call(["open", path])
    else:
        subprocess.call(["xdg-open", path])

def safe_float(v):
    try:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            v = v.replace(".", "").replace(",", "").strip()
            return float(v) if v else None
    except Exception:
        return None
    return None

# ============================================================
# DISCOVERY
# ============================================================

def discover_peek_cases(root):
    cases = []

    for dirpath, _, filenames in os.walk(root):
        if PEEK_CASE_FILE in filenames:
            case_id = os.path.basename(dirpath)
            client_id = os.path.basename(os.path.dirname(dirpath))
            peek_path = os.path.join(dirpath, PEEK_CASE_FILE)

            case = {
                "case_id": case_id,
                "client_id": client_id,
                "path": dirpath,
                "peek_path": peek_path,
                "peek": load_json(peek_path, {}) or {}
            }

            autofill_ids_from_folder(case)
            cases.append(case)

    return cases

# ============================================================
# AUTOFILL IDS
# ============================================================

def autofill_ids_from_folder(case):
    case_id = case["case_id"]
    parts = case_id.split("-")
    peek = case["peek"]
    changed = False

    if not peek.get("id_caso"):
        peek["id_caso"] = case_id
        changed = True

    if len(parts) >= 2 and not peek.get("doctor_id"):
        peek["doctor_id"] = parts[1]
        changed = True

    if changed:
        peek["actualizado_en"] = iso_now()
        save_json(case["peek_path"], peek)

# ============================================================
# LEGACY INITIALIZER
# ============================================================

def init_peek_case_if_missing(case_path, clients_db):
    peek_path = os.path.join(case_path, PEEK_CASE_FILE)
    if os.path.exists(peek_path):
        return False

    case_id = os.path.basename(case_path)
    parts = case_id.split("-")

    peek = {
        "id_caso": case_id,
        "doctor_id": "",
        "nombre_doctor": "",
        "hospital_clinica": "",
        "nombre_paciente": "",
        "fecha_cirugia": "",
        "fecha_entrega_estimada": "",
        "region": "",
        "especificaciones": "",
        "precio_clp": "",
        "origen": "legacy_init",
        "creado_en": iso_now(),
        "actualizado_en": iso_now(),
    }

    if len(parts) >= 2:
        doctor_id = parts[1]
        peek["doctor_id"] = doctor_id
        doctor = clients_db.get(doctor_id, {})
        if isinstance(doctor, dict):
            peek["nombre_doctor"] = (
                doctor.get("nombre")
                or doctor.get("name")
                or ""
            )

    save_json(peek_path, peek)
    return True

def init_missing_peek_cases(root):
    clients_db = load_json(CLIENTS_FILE, {}) or {}
    created = 0

    for dirpath, _, filenames in os.walk(root):
        if PEEK_CASE_FILE not in filenames:
            created += int(init_peek_case_if_missing(dirpath, clients_db))

    print(f"[✓] Initialized {created} peekCase.json files.")

# ============================================================
# FIELD HELPERS
# ============================================================

def prompt_date(label, current):
    raw = input(f"{label} [{current}]: ").strip()
    if not raw:
        return current
    try:
        datetime.datetime.strptime(raw, DATE_FMT_INTERNAL)
        return raw
    except ValueError:
        print("Formato inválido. Use YYYY-MM-DD.")
        return current

def select_from_dict(title, items: dict, current=""):
    keys = sorted(items.keys())
    print(f"\n{title}:")
    for i, k in enumerate(keys, 1):
        name = items[k].get("name") or items[k].get("nombre") or k
        print(f"{i}. {name} ({k})")

    sel = input(f"> [{current}] ").strip()
    if not sel:
        return current

    if sel.isdigit() and 1 <= int(sel) <= len(keys):
        k = keys[int(sel)-1]
        return items[k].get("name") or items[k].get("nombre") or k

    return current

# ============================================================
# PEEK EDITOR
# ============================================================

def peek_editor(case):
    peek = case["peek"]
    peek_path = case["peek_path"]

    clients   = load_json(CLIENTS_FILE, {}) or {}
    hospitals = load_json(HOSPITALS_FILE, {}) or {}

    fields = list(peek.keys())

    def edit_field(k):
        old = peek.get(k, "")
        if k == "nombre_doctor":
            new = select_from_dict("Seleccionar Doctor", clients, old)
        elif k == "hospital_clinica":
            new = select_from_dict("Seleccionar Hospital", hospitals, old)
        elif k in ("fecha_cirugia", "fecha_entrega_estimada"):
            new = prompt_date(k, old)
        else:
            new = input(f"{k} [{old}]: ").strip() or old

        if new != old:
            peek[k] = new
            peek["actualizado_en"] = iso_now()

    while True:
        print("\n=== PEEK Case Editor ===")
        print(f"{case['case_id']} ({case['client_id']})")
        print("1. Recorrer todos los campos")
        print("2. Recorrer campos vacíos")
        print("3. Recorrer campos llenos")
        print("4. Editar campo específico")
        print("[B] Volver")

        c = input("> ").strip().lower()

        if c == "1":
            for k in fields:
                edit_field(k)
            save_json(peek_path, peek)

        elif c == "2":
            for k in fields:
                if not peek.get(k):
                    edit_field(k)
            save_json(peek_path, peek)

        elif c == "3":
            for k in fields:
                if peek.get(k):
                    edit_field(k)
            save_json(peek_path, peek)

        elif c == "4":
            for i, k in enumerate(fields, 1):
                print(f"{i}. {k} = {peek.get(k)}")
            sel = input("> ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(fields):
                edit_field(fields[int(sel)-1])
                save_json(peek_path, peek)

        elif c == "b":
            break

# ============================================================
# EXPORT
# ============================================================

def format_date_hq(iso_date):
    if not iso_date:
        return ""
    try:
        d = datetime.datetime.strptime(iso_date, "%Y-%m-%d")
        return d.strftime("%d/%m/%y")
    except ValueError:
        return ""

def extract_dc(case_id):
    try:
        part = case_id.split("-")[0]
        return part[:2] + part[2:].lstrip("0")
    except Exception:
        return ""

def export_peek_cases_csv(cases, month=None, year=None):
    out_dir = os.path.join(ROOT, "_Exports")
    os.makedirs(out_dir, exist_ok=True)

    out_name = "PEEK_ALL.csv"
    if month and year:
        out_name = f"PEEK_{year}_{str(month).zfill(2)}.csv"

    out_path = os.path.join(out_dir, out_name)

    header = [
        "ID del Caso",
        "Nombre del Doctor",
        "Hospital",
        "Nombre del Paciente",
        "Contacto",
        "Fecha Ingreso",
        "Fecha Entrega",
        "DC (date code)",
        "Fecha Cirugía",
        "Descripcion",
        "Precio Implante (IVA Incluido)",
        "Neto",
        "Comision Sugerida"
    ]

    rows = [header]

    for c in cases:
        peek = c["peek"]
        fecha_cx = peek.get("fecha_cirugia", "")

        if month and year:
            if not fecha_cx.startswith(f"{year}-{str(month).zfill(2)}"):
                continue

        precio = safe_float(peek.get("precio_clp"))
        neto = round(precio / IVA) if precio else ""

        desc = f"{peek.get('region','')} - {peek.get('especificaciones','')} - PEEK"
        desc = desc.strip(" -")

        rows.append([
            c["case_id"],
            peek.get("nombre_doctor", ""),
            peek.get("hospital_clinica", ""),
            peek.get("nombre_paciente", ""),
            "",
            "",
            format_date_hq(peek.get("fecha_entrega_estimada", "")),
            extract_dc(c["case_id"]),
            format_date_hq(fecha_cx),
            desc,
            f"${precio:,.0f}".replace(",", ".") if precio else "",
            f"${neto:,.0f}".replace(",", ".") if neto else "",
            ""
        ])

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=";").writerows(rows)

    print(f"[✓] Export generado: {out_path}")

# ============================================================
# UI HELPERS
# ============================================================

def select_case(cases):
    term = input("Filter by case ID (Enter = all): ").strip().lower()
    items = [c for c in cases if term in c["case_id"].lower()] if term else cases

    if not items:
        return None

    for i, c in enumerate(items[:12], 1):
        print(f"{i}. {c['case_id']} | {c['client_id']} | {c['peek'].get('fecha_cirugia','')}")

    sel = input("> ").strip()
    if sel.isdigit() and 1 <= int(sel) <= len(items):
        return items[int(sel)-1]
    return None

# ============================================================
# MAIN
# ============================================================

def main():
    cases = discover_peek_cases(ROOT)

    while True:
        print("\n=== PEEK REGISTRY ===")
        print("1. Open / Edit Case")
        print("2. Export report")
        print("3. Initialize missing peekCase.json (legacy)")
        print("4. Reload from disk")
        print("5. Exit")

        c = input("> ").strip()

        if c == "1":
            case = select_case(cases)
            if case:
                peek_editor(case)

        elif c == "2":
            print("\nExport:")
            print("1. Export all")
            print("2. Export by month/year")
            print("[B] Back")

            e = input("> ").strip().lower()
            if e == "1":
                export_peek_cases_csv(cases)
            elif e == "2":
                y = input("Year (YYYY): ").strip()
                m = input("Month (MM): ").strip()
                if y.isdigit() and m.isdigit():
                    export_peek_cases_csv(cases, int(m), int(y))

        elif c == "3":
            init_missing_peek_cases(ROOT)
            cases = discover_peek_cases(ROOT)

        elif c == "4":
            cases = discover_peek_cases(ROOT)
            print("[✓] Reloaded from disk.")

        elif c == "5":
            break

if __name__ == "__main__":
    main()
