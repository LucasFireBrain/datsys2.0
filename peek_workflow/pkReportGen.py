import os
import json
import csv
import argparse
import datetime

# ==================================================
# CONFIG
# ==================================================

ROOT = r"C:\Users\Lucas\Desktop\Hexamod\Clients\Hexamod\Datsys"
PEEK_CASE_FILE = "peekCase.json"
IVA = 1.19

# ==================================================
# HELPERS
# ==================================================

def load_json(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def format_date_hq(iso_date):
    if not iso_date:
        return ""
    try:
        d = datetime.datetime.strptime(iso_date, "%Y-%m-%d")
        return d.strftime("%d/%m/%y")
    except ValueError:
        return ""

def extract_dc(case_id):
    # PC03-XXX-PK1 → PC3
    try:
        part = case_id.split("-")[0]
        return part[:2] + part[2:].lstrip("0")
    except Exception:
        return ""

# ==================================================
# CORE EXPORT
# ==================================================

def export_peek_cases(month=None, year=None, export_all=False):
    out_dir = os.path.join(ROOT, "Exports")
    os.makedirs(out_dir, exist_ok=True)

    if export_all:
        out_name = "PEEK_ALL.csv"
    else:
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

    for client_id in os.listdir(ROOT):
        client_path = os.path.join(ROOT, client_id)
        if not os.path.isdir(client_path):
            continue

        for case_id in os.listdir(client_path):
            case_path = os.path.join(client_path, case_id)
            if not os.path.isdir(case_path):
                continue

            peek_path = os.path.join(case_path, PEEK_CASE_FILE)
            peek = load_json(peek_path)
            if not peek:
                continue

            fecha_cx = peek.get("fecha_cirugia", "")
            if not export_all:
                if not fecha_cx.startswith(f"{year}-{str(month).zfill(2)}"):
                    continue

            precio = peek.get("precio_clp", 0)
            neto = round(precio / IVA) if precio else ""

            descripcion = f"{peek.get('region','')} - {peek.get('especificaciones','')} - PEEK"
            descripcion = descripcion.strip(" -")

            rows.append([
                case_id,
                peek.get("nombre_doctor", ""),
                peek.get("hospital_clinica", ""),
                peek.get("nombre_paciente", ""),
                "",
                "",
                format_date_hq(peek.get("fecha_entrega_estimada", "")),
                extract_dc(case_id),
                format_date_hq(fecha_cx),
                descripcion,
                f"${precio:,.0f}".replace(",", ".") if precio else "",
                f"${neto:,.0f}".replace(",", ".") if neto else "",
                ""
            ])

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(rows)

    print(f"[✓] Export generado: {out_path}")

# ==================================================
# CLI
# ==================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PEEK Report Generator")
    parser.add_argument("--month", type=int, help="Mes (MM)")
    parser.add_argument("--year", type=int, help="Año (YYYY)")
    parser.add_argument("--all", action="store_true", help="Exportar todos los casos")

    args = parser.parse_args()

    if args.all:
        export_peek_cases(export_all=True)
    else:
        if args.month is None or args.year is None:
            print("Error: use --all OR --month MM --year YYYY")
        else:
            export_peek_cases(month=args.month, year=args.year)
