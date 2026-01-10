import os, json, datetime, random, string
from idHelper import prompt_client_id, make_project_id as _old_make_project_id  # if you had one
from peek_workflow.peek_workflow import run_peek_initialization, import_dicom_into_project

# ----------------------------
# Constants
# ----------------------------
CONFIG_FILE   = "config.json"
CLIENTS_FILE  = "clients.json"
PROJECTS_FILE = "projects.json"
RECENTS_FILE  = "recents.json"
TEMPLATES_DIR = "templates"

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# ----------------------------
# JSON Helpers
# ----------------------------
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def load_json(path, default):
    if not os.path.exists(path):
        save_json(path, default)
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ----------------------------
# Date / ID Helpers
# ----------------------------
def to_base36(n: int) -> str:
    if n < 0 or n >= 36:
        raise ValueError("to_base36 expects 0–35")
    return DIGITS[n]

def today_date_code() -> str:
    """Return date code like PC03 (P=25, C=12, 03=day)."""
    now = datetime.datetime.now()
    yy = now.year % 100
    mm = now.month
    dd = now.day
    y_char = to_base36(yy)    # 25 -> 'P'
    m_char = to_base36(mm)    # 12 -> 'C'
    return f"{y_char}{m_char}{dd:02d}"

def iso_now():
    return datetime.datetime.now().isoformat()

def iso_to_short(iso_str: str) -> str:
    """2025-12-03T... -> 251203"""
    try:
        dt = datetime.datetime.fromisoformat(iso_str)
        return dt.strftime("%y%m%d")
    except Exception:
        return "------"

def make_project_id(client_id, existing_pids_for_client, type_letter):
    """
    Project ID pattern:
      <DATECODE>-<CLIENTID>-<TYPE><N>
    Example:
      PC03-CLX-PK1
    Counter is 1–9 based on how many projects already exist
    for this client with the same date code.
    """
    date_code = today_date_code()  # e.g. PC03
    prefix = f"{date_code}-{client_id}-"

    # Count existing projects for this client *for this date_code*
    count = 0
    for pid in existing_pids_for_client:
        if pid.startswith(prefix):
            count += 1

    counter = count + 1
    if counter > 9:
        print("[!] More than 9 projects for this client/date. Counter > 9.")
    return f"{prefix}{type_letter}{counter}"

# ----------------------------
# Init Environment
# ----------------------------
def init_environment():
    ensure_dir(TEMPLATES_DIR)

    default_template_path = os.path.join(TEMPLATES_DIR, "default.json")
    if not os.path.exists(default_template_path):
        default_template = {
            "name": "Default Engineering Project",
            "subfolders": ["Docs", "Exports", "Work"],
            "files": {"README.txt": "This is a new project initialized by DATSYS."}
        }
        save_json(default_template_path, default_template)

    if not os.path.exists(CONFIG_FILE):
        save_json(CONFIG_FILE, {"root_path": "", "current_user": ""})
    if not os.path.exists(CLIENTS_FILE):
        save_json(CLIENTS_FILE, {})
    if not os.path.exists(PROJECTS_FILE):
        save_json(PROJECTS_FILE, {})
    if not os.path.exists(RECENTS_FILE):
        save_json(RECENTS_FILE, {"steps": []})

# ----------------------------
# Load DB
# ----------------------------
def load_all():
    config   = load_json(CONFIG_FILE, {"root_path": "", "current_user": ""})
    clients  = load_json(CLIENTS_FILE, {})
    projects = load_json(PROJECTS_FILE, {})
    recents  = load_json(RECENTS_FILE, {"steps": []})
    return config, clients, projects, recents

# ----------------------------
# Client Selection (Paged)
# ----------------------------
def select_client(clients):
    """
    Paginated client selector.
    Returns client_id or None if cancelled.
    """
    if not clients:
        print("[!] No clients yet.")
        return None

    client_ids = list(clients.keys())  # insertion order preserved
    page = 0
    page_size = 9

    while True:
        start = page * page_size
        end = start + page_size
        page_clients = client_ids[start:end]

        if not page_clients:
            print("[!] No more clients.")
            return None

        total_pages = (len(client_ids) - 1) // page_size + 1
        print("\n=== Clients (page {} of {}) ===".format(page + 1, total_pages))

        for idx, cid in enumerate(page_clients, 1):
            data = clients[cid]
            name = data.get("name", "")
            print(f"{idx}. {cid} - {name}")

        print("\nChoose [1-9], 'n' (next), 'b' (back), or 'q' (cancel)")
        choice = input("> ").strip().lower()

        if choice == "q":
            return None
        elif choice == "n":
            page += 1
        elif choice == "b":
            if page > 0:
                page -= 1
        elif choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(page_clients):
                return page_clients[num - 1]
            else:
                print("[!] Invalid number.")
        else:
            print("[!] Invalid input.")

# ----------------------------
# Client Management
# ----------------------------
def new_client(config, clients):
    name = input("Enter client full name: ").strip()
    if not name:
        print("[!] Name required.")
        return

    cid = prompt_client_id(name, set(clients.keys()))
    while len(cid) < 3:
        print("[!] Client ID must be at least 3 characters.")
        cid = input("Enter client ID (>=3 chars): ").strip()

    email   = input("Enter email (optional): ").strip()
    phone   = input("Enter phone (optional): ").strip()
    contact = input("Enter main contact person (optional): ").strip()
    notes   = input("Notes (optional): ").strip()

    clients[cid] = {
        "id": cid,
        "name": name,
        "email": email,
        "phone": phone,
        "contact": contact,
        "notes": notes,
        "projects": []
    }
    save_json(CLIENTS_FILE, clients)

    client_path = os.path.join(config["root_path"], cid)
    ensure_dir(client_path)
    print(f"[✓] Client {cid} created at {client_path}")

def list_clients(clients):
    if not clients:
        print("(No clients yet)")
        return
    print("\n=== Clients (older first) ===")
    for cid, data in clients.items():
        print(f"- {cid}: {data['name']} ({len(data.get('projects', []))} projects)")

# ----------------------------
# Project Selection (Recent)
# ----------------------------
def select_project(projects):
    """
    Show projects sorted by last_opened (or created_at), most recent first.
    Returns project_id or None.
    """
    if not projects:
        print("[!] No projects yet.")
        return None

    # Build sortable list
    def sort_key(item):
        pid, data = item
        ts = data.get("last_opened") or data.get("created_at") or ""
        return ts

    items = sorted(projects.items(), key=sort_key, reverse=True)
    page = 0
    page_size = 9

    while True:
        start = page * page_size
        end = start + page_size
        page_items = items[start:end]

        if not page_items:
            print("[!] No more projects.")
            return None

        total_pages = (len(items) - 1) // page_size + 1
        print("\n=== Recent Projects (page {} of {}) ===".format(page + 1, total_pages))

        for idx, (pid, data) in enumerate(page_items, 1):
            cid = data.get("client_id", "")
            created = data.get("created_at", "")
            last_opened = data.get("last_opened", created)
            short_date = iso_to_short(last_opened)
            print(f"{idx}. {pid} (Client: {cid}) [{short_date}]")

        print("\nChoose [1-9], 'n' (next), 'b' (back), or 'q' (cancel)")
        choice = input("> ").strip().lower()

        if choice == "q":
            return None
        elif choice == "n":
            page += 1
        elif choice == "b":
            if page > 0:
                page -= 1
        elif choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(page_items):
                return page_items[num - 1][0]  # return project_id
            else:
                print("[!] Invalid number.")
        else:
            print("[!] Invalid input.")

# ----------------------------
# Project Management
# ----------------------------
def new_project(config, clients, projects):
    # Ensure we have at least one client
    if not clients:
        print("[!] No clients available.")
        create = input("Create new client? [y/N] ").strip().lower()
        if create == "y":
            new_client(config, clients)
        else:
            return

    # Ask for client ID or list
    cid_input = input("Enter client ID (or press Enter to choose from list): ").strip()
    if cid_input:
        if cid_input in clients:
            client_id = cid_input
        else:
            print(f"[i] Client '{cid_input}' not found.")
            create = input("Create new client with this ID? [y/N] ").strip().lower()
            if create == "y":
                # minimal creation using this ID
                name = input("Enter full name for this client: ").strip() or cid_input
                clients[cid_input] = {
                    "id": cid_input,
                    "name": name,
                    "email": "",
                    "phone": "",
                    "contact": "",
                    "notes": "",
                    "projects": []
                }
                save_json(CLIENTS_FILE, clients)
                client_id = cid_input
            else:
                return
    else:
        client_id = select_client(clients)
        if not client_id:
            print("[i] Cancelled.")
            return

    # Choose project type
    print("\nProject types:")
    print("X  = Default")
    print("A  = Arduino")
    print("PK = PEEK Case (workflow enabled)")
    type_letter = input("Enter project type [X]: ").strip().upper() or "X"

    # Build project id
    existing_pids_for_client = clients[client_id].get("projects", [])
    project_id = make_project_id(client_id, existing_pids_for_client, type_letter)

    confirm = input(f"Confirm or enter different Project ID [{project_id}]: ").strip()
    if confirm:
        project_id = confirm

    # Create project folder and basic scaffold
    project_path = os.path.join(config["root_path"], client_id, project_id)
    ensure_dir(project_path)

    logs_folder = os.path.join(project_path, "logs")
    ensure_dir(logs_folder)

    protocol_path = os.path.join(project_path, "protocol.json")
    if not os.path.exists(protocol_path):
        save_json(protocol_path, {"steps": []})

    now_iso = iso_now()

    local_meta = {
        "id": project_id,
        "client_id": client_id,
        "created_at": now_iso,
        "last_updated": now_iso,
        "created_by": config["current_user"],
        "status": "open",
        "tags": [],
        "template": type_letter,
        "protocol": "protocol.json",
        "logs": []
    }

    local_meta_path = os.path.join(project_path, f"{project_id}.json")
    save_json(local_meta_path, local_meta)

    projects[project_id] = {
        "id": project_id,
        "client_id": client_id,
        "path": project_path,
        "created_at": now_iso,
        "last_opened": now_iso,
        "template": type_letter
    }
    save_json(PROJECTS_FILE, projects)

    clients[client_id].setdefault("projects", []).append(project_id)
    save_json(CLIENTS_FILE, clients)

    print(f"[✓] Project {project_id} created under client {client_id}")

    # Run PEEK workflow if needed
    if type_letter == "PK":
        run_peek_initialization(project_path, project_id)
        print("[✓] PEEK workflow initialized.")

def open_project(projects):
    pid = select_project(projects)
    if not pid:
        print("[i] Cancelled.")
        return

    proj = projects[pid]
    project_path = proj["path"]
    print(f"\n=== Project: {pid} ===")
    print(f"Path: {project_path}")

    # Update last_opened
    proj["last_opened"] = iso_now()
    save_json(PROJECTS_FILE, projects)

    # Optionally open OS file explorer (Windows only)
    if os.name == "nt":
        choice = input("Open folder in Explorer? [y/N]: ").strip().lower()
        if choice == "y":
            os.startfile(project_path)

def list_projects(projects):
    if not projects:
        print("(No projects yet)")
        return

    print("\n=== Projects ===")
    for pid, data in projects.items():
        cid = data.get("client_id", "")
        created = data.get("created_at", "")
        short_date = iso_to_short(created)
        print(f"- {pid} (Client: {cid}) [{short_date}]")

# ----------------------------
# Logs
# ----------------------------
def make_log_id():
    now = datetime.datetime.now()
    base = now.strftime("%y%m%d-%H%M%S")
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"{base}-{suffix}"

def add_log(config, projects, recents):
    if not projects:
        print("No projects available.")
        return

    pids = list(projects.keys())
    for i, pid in enumerate(pids, 1):
        print(f"{i}. {pid} (Client: {projects[pid]['client_id']})")

    choice = input("Choose project number: ").strip()

    try:
        pid = pids[int(choice)-1]
    except:
        print("Invalid choice.")
        return

    project = projects[pid]
    project_file = os.path.join(project["path"], f"{pid}.json")

    if not os.path.exists(project_file):
        print("[!] Project metadata missing.")
        return

    local_meta = load_json(project_file, {})

    print("\nRecent Steps:")
    for i, step in enumerate(recents["steps"], 1):
        print(f"{i}. {step}")

    step = input("Choose [1-9] or type new step: ").strip()

    if step.isdigit() and 1 <= int(step) <= len(recents["steps"]):
        step = recents["steps"][int(step)-1]

    notes = input("Notes: ").strip()

    log_id = make_log_id()
    timestamp = iso_now()

    img_folder = os.path.join(project["path"], "logs", f"{log_id}_img")
    ensure_dir(img_folder)

    log_entry = {
        "log_id": log_id,
        "timestamp": timestamp,
        "user": config["current_user"],
        "step": step,
        "notes": notes,
        "images": []
    }

    local_meta.setdefault("logs", []).append(log_entry)
    local_meta["last_updated"] = timestamp
    save_json(project_file, local_meta)

    if step and step not in recents["steps"]:
        recents["steps"].insert(0, step)
        recents["steps"] = recents["steps"][:9]
        save_json(RECENTS_FILE, recents)

    print(f"[✓] Log added: {step} (ID: {log_id})")
    print(f"    Image folder created: {img_folder}")

# ----------------------------
# View Logs
# ----------------------------
def view_logs(projects):
    if not projects:
        print("No projects available.")
        return

    pids = list(projects.keys())
    for i, pid in enumerate(pids, 1):
        print(f"{i}. {pid}")

    choice = input("Choose project number: ").strip()

    try:
        pid = pids[int(choice)-1]
    except:
        print("Invalid choice.")
        return

    project_file = os.path.join(projects[pid]["path"], f"{pid}.json")
    if not os.path.exists(project_file):
        print("[!] Project metadata missing.")
        return

    local_meta = load_json(project_file, {})
    print(f"\n=== Logs for {pid} ===")

    for log in local_meta.get("logs", []):
        print(f"{log['log_id']} | {log['user']} | {log['step']} | {log['notes']}")

# ----------------------------
# IMPORT DICOM LATER
# ----------------------------
def import_dicom_later(projects):
    if not projects:
        print("No projects available.")
        return

    pids = list(projects.keys())
    for i, pid in enumerate(pids, 1):
        print(f"{i}. {pid}")

    choice = input("Choose project number: ").strip()

    try:
        pid = pids[int(choice)-1]
    except:
        print("Invalid choice.")
        return

    project = projects[pid]
    project_path = project["path"]

    print(f"\n=== Importing DICOM into {pid} ===\n")
    import_dicom_into_project(project_path)

# ----------------------------
# Main
# ----------------------------
def main():
    init_environment()
    config, clients, projects, recents = load_all()

    if not config["current_user"]:
        config["current_user"] = input("Enter your username: ").strip()
        save_json(CONFIG_FILE, config)

    if not config["root_path"]:
        config["root_path"] = input("Enter root path for clients/projects: ").strip()
        save_json(CONFIG_FILE, config)

    while True:
        print("\n=== DATSYS Main Menu ===")
        print("1. New Project")
        print("2. Open Project (recent)")
        print("3. New Client")
        print("4. List Clients")
        print("5. List Projects")
        print("6. Add Execution Log")
        print("7. View Logs")
        print("8. Import DICOM Into Existing Project")
        print("9. Exit")

        choice = input("> ").strip()

        if choice == "1":
            new_project(config, clients, projects)
        elif choice == "2":
            open_project(projects)
        elif choice == "3":
            new_client(config, clients)
        elif choice == "4":
            list_clients(clients)
        elif choice == "5":
            list_projects(projects)
        elif choice == "6":
            add_log(config, projects, recents)
        elif choice == "7":
            view_logs(projects)
        elif choice == "8":
            import_dicom_later(projects)
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
