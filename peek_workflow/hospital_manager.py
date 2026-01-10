import json
import os

HOSPITALS_FILE = "hospitals.json"

FIELDS = [
    "codigo",
    "nombre",
    "direccion",
    "horario_atencion",
    "esterilizacion",
    "piso_pabellon",
    "dias_anticipacion",
    "notas"
]

# -------------------------
# IO helpers
# -------------------------

def load_hospitals():
    if not os.path.exists(HOSPITALS_FILE):
        return {}
    with open(HOSPITALS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_hospitals(data):
    with open(HOSPITALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -------------------------
# edit logic
# -------------------------

def edit_hospital(hospital):
    print("\n--- Editando hospital ---")
    for field in FIELDS:
        current = hospital.get(field, "")
        value = input(f"{field} [{current}]: ").strip()
        if value:
            hospital[field] = value

# -------------------------
# main
# -------------------------

def main():
    hospitals = load_hospitals()

    while True:
        print("\n=== HOSPITAL MANAGER ===")
        print("1. Listar hospitales")
        print("2. Editar / Crear hospital")
        print("3. Guardar y salir")

        c = input("> ").strip()

        if c == "1":
            if not hospitals:
                print("(sin hospitales)")
            for code, h in hospitals.items():
                print(f"{code} - {h.get('nombre','')}")

        elif c == "2":
            code = input("Código hospital: ").strip().upper().replace(" ", "")
            if not code:
                continue

            if code in hospitals:
                edit_hospital(hospitals[code])
            else:
                yn = input("No existe. ¿Crear nuevo? [y/N]: ").strip().lower()
                if yn == "y":
                    hospitals[code] = {f: "" for f in FIELDS}
                    hospitals[code]["codigo"] = code
                    edit_hospital(hospitals[code])

        elif c == "3":
            save_hospitals(hospitals)
            print("Guardado.")
            break

if __name__ == "__main__":
    main()
