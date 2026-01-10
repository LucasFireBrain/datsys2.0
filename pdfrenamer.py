import os
import re
from pypdf import PdfReader

# =========================
# CONFIG
# =========================
INPUT_DIR = r"C:\Users\Lucas\Desktop\gastos comunes vecina 512\Pagos"
DRY_RUN = True  # <-- SET TO False when confident

# =========================
# REGEX
# =========================
DATE_REGEX = re.compile(
    r"fecha\s+de\s+movimiento\s+(\d{2})/(\d{2})/(\d{4})",
    re.IGNORECASE
)

# =========================
# HELPERS
# =========================
def safe_filename(path):
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path
    while os.path.exists(new_path):
        new_path = f"{base}_{counter}{ext}"
        counter += 1
    return new_path

# =========================
# MAIN
# =========================
for fname in os.listdir(INPUT_DIR):
    if not fname.lower().endswith(".pdf"):
        continue

    full_path = os.path.join(INPUT_DIR, fname)

    try:
        reader = PdfReader(full_path)
        if not reader.pages:
            print(f"Skipping empty PDF: {fname}")
            continue

        text = reader.pages[0].extract_text() or ""
        match = DATE_REGEX.search(text)

        if not match:
            print(f"⚠ Fecha not found: {fname}")
            continue

        day, month, year = match.groups()
        new_name = f"{year}-{month}-{day}_Comprobante.pdf"
        new_path = safe_filename(os.path.join(INPUT_DIR, new_name))

        if DRY_RUN:
            print(f"[DRY] {fname}  →  {os.path.basename(new_path)}")
        else:
            os.rename(full_path, new_path)
            print(f"RENAMED: {fname} → {os.path.basename(new_path)}")

    except Exception as e:
        print(f"❌ Error processing {fname}: {e}")

print("\nDone.")
