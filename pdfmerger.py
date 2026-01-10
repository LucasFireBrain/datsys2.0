import os
import re
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# =========================
# CONFIG
# =========================
INPUT_DIR = r"C:\Users\Lucas\Desktop\gastos comunes vecina 512"
OUTPUT_PDF = "interlaced_chronological.pdf"

# =========================
# REGEX
# =========================
RE_FECHA_MOV = re.compile(
    r"fecha\s+de\s+movimiento\s+(\d{2})/(\d{2})/(\d{4})",
    re.IGNORECASE
)

RE_VENCIMIENTO = re.compile(
    r"vencimiento\s*:\s*(\d{2})/(\d{2})/(\d{4})",
    re.IGNORECASE
)

MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

RE_MES_COBRO = re.compile(
    r"mes\s+de\s+cobro\s*:\s*([a-záéíóú]+)\s*-\s*(\d{4})",
    re.IGNORECASE
)

# =========================
# DATE EXTRACTION
# =========================
def extract_date(text):
    # Banco de Chile payment
    m = RE_FECHA_MOV.search(text)
    if m:
        d, mth, y = m.groups()
        return datetime(int(y), int(mth), int(d)), "payment"

    # Gastos comunes vencimiento
    m = RE_VENCIMIENTO.search(text)
    if m:
        d, mth, y = m.groups()
        return datetime(int(y), int(mth), int(d)), "bill"

    # Gastos comunes mes de cobro (fallback → first day of month)
    m = RE_MES_COBRO.search(text)
    if m:
        month_name, year = m.groups()
        month = MONTHS.get(month_name.lower())
        if month:
            return datetime(int(year), month, 1), "bill"

    return None, None

# =========================
# COLLECT TIMELINE ITEMS
# =========================
items = []

for fname in os.listdir(INPUT_DIR):
    if not fname.lower().endswith(".pdf"):
        continue

    path = os.path.join(INPUT_DIR, fname)

    try:
        reader = PdfReader(path)
        if not reader.pages:
            continue

        text = reader.pages[0].extract_text() or ""
        date, doc_type = extract_date(text)

        if not date:
            print(f"⚠ Date not found: {fname}")
            continue

        items.append({
            "date": date,
            "type": doc_type,
            "path": path
        })

        print(f"✔ {doc_type.upper()} | {date.date()} | {fname}")

    except Exception as e:
        print(f"❌ Error reading {fname}: {e}")

# =========================
# SORT & MERGE
# =========================
items.sort(key=lambda x: x["date"])

writer = PdfWriter()

for item in items:
    reader = PdfReader(item["path"])
    writer.add_page(reader.pages[0])

with open(os.path.join(INPUT_DIR, OUTPUT_PDF), "wb") as f:
    writer.write(f)

print("\nDONE →", OUTPUT_PDF)
