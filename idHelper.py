import datetime

# ----------------------------
# Base36 Helper
# ----------------------------
def base36(num: int) -> str:
    """Convert integer to base36 string."""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if num == 0:
        return "0"
    digits = []
    while num > 0:
        num, rem = divmod(num, 36)
        digits.append(chars[rem])
    return "".join(reversed(digits))

# ----------------------------
# Client ID Helper
# ----------------------------
def suggest_client_id(name: str, existing_ids: set) -> str:
    """Suggest a unique ID based on name initials, adjusted if needed."""
    parts = name.strip().split()
    if len(parts) == 1:
        base = parts[0][:3].upper()
    else:
        base = (parts[0][0] + parts[-1][0] + parts[-1][-1]).upper()

    suggestion = base
    counter = 1
    while suggestion in existing_ids:
        suggestion = f"{base}{counter}"
        counter += 1
    return suggestion

def prompt_client_id(name: str, existing_ids: set) -> str:
    """Prompt user with a safe suggestion, allow override."""
    suggestion = suggest_client_id(name, existing_ids)
    while True:
        cid = input(f"Enter Client ID [{suggestion}]: ").strip().upper()
        if not cid:
            return suggestion
        if cid in existing_ids:
            print(f"[!] Client ID {cid} already exists. Try again.")
            continue
        return cid

# ----------------------------
# Project ID Helper
# ----------------------------
def make_project_id(client_id: str, project_count: int, type_letter: str) -> str:
    """Generate a project ID based on date, client, and count."""
    today = datetime.date.today().strftime("%y%m%d")
    counter = base36(project_count + 1)
    return f"{today}-{client_id}-{type_letter.upper()}{counter}"
