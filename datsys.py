import os, json, datetime, random, string
from idHelper import prompt_client_id, make_project_id

# ----------------------------
# Constants
# ----------------------------
CONFIG_FILE   = "config.json"
CLIENTS_FILE  = "clients.json"
PROJECTS_FILE = "projects.json"
RECENTS_FILE  = "recents.json"
TEMPLATES_DIR = "templates"

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
# Init Environment
# ----------------------------
def init_environment():
    ensure_dir(TEMPLATES_DIR)

    # default template
    default_template_path = os.path.join(TEMPLATES_DIR, "default.json")
    if not os.path.exists(default_template_path):
        default_template = {
            "name": "Default Engineering Project",
            "subfolders": ["Docs", "Exports", "Work"],
            "files": {"README.txt": "This is a new project initialized by DATSYS."}
        }
        save_json(default_template_path, default_template)
        print("[✓] Default template created at templates/default.json")

    # core DB files
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
# Client Management
# ----------------------------
def new_client(config, clients):
    name = input("Enter client full name: ").strip()
    if not name:
        print("[!] Name required.")
        return

    cid = prompt_client_id(name, set(clients.keys()))
    email   = input("Enter email: ").strip()
    phone   = input("Enter phone: ").strip()
    contact = input("Enter main contact person: ").strip()
    notes   = input("Notes: ").strip()

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
    for cid, data in clients.items():
        print(f"- {cid}: {data['name']} ({len(data['projects'])} projects)")

# ----------------------------
# Project Management
# ----------------------------
def new_project(config, clients, projects):
    if not clients:
        print("No clients available.")
        return

    # select client
    cids = list(clients.keys())
    for i, cid in enumerate(cids, 1):
        print(f"{i}. {cid} ({clients[cid]['name']})")
    choice = input("Choose client number: ").strip()
    try:
        client_id = cids[int(choice)-1]
    except:
        print("Invalid choice.")
        return

    type_letter = input("Enter project type letter (P=PEEK, A=Arduino, X=Default): ").strip() or "X"
    project_count = len(clients[client_id]["projects"])
    project_id = make_project_id(client_id, project_count, type_letter)

    confirm = input(f"Confirm or enter different Project ID [{project_id}]: ").strip()
    if confirm:
        project_id = confirm

    # create project folder
    project_path = os.path.join(config["root_path"], client_id, project_id)
    ensure_dir(project_path)

    # create logs folder
    logs_folder = os.path.join(project_path, "logs")
    ensure_dir(logs_folder)

    # create protocol.json
    protocol_path = os.path.join(project_path, "protocol.json")
    if not os.path.exists(protocol_path):
        save_json(protocol_path, {"steps": []})

    now = datetime.datetime.now().isoformat()

    # local project metadata
    local_meta = {
        "id": project_id,
        "client_id": client_id,
        "created_at": now,
        "last_updated": now,
        "created_by": config["current_user"],
        "status": "open",
        "tags": [],
        "template": "default.json",
        "protocol": "protocol.json",
        "logs": []
    }
    local_meta_path = os.path.join(project_path, f"{project_id}.json")
    save_json(local_meta_path, local_meta)

    # update global projects index
    projects[project_id] = {
        "id": project_id,
        "client_id": client_id,
        "path": project_path,
        "created_at": now,
        "created_by": config["current_user"],
        "template": "default.json"
    }
    save_json(PROJECTS_FILE, projects)

    # update client reference
    clients[client_id]["projects"].append(project_id)
    save_json(CLIENTS_FILE, clients)

    print(f"[✓] Project {project_id} created under client {client_id}")

def list_projects(projects):
    if not projects:
        print("(No projects yet)")
        return
    for pid, data in projects.items():
        print(f"- {pid} (Client: {data['client_id']}, Path: {data['path']})")

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

    # select project
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

    # generate log_id + timestamp
    log_id = make_log_id()
    timestamp = datetime.datetime.now().isoformat()

    # create image folder
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
        img_folder = os.path.join(projects[pid]["path"], "logs", f"{log['log_id']}_img")
        if os.path.exists(img_folder):
            log["images"] = os.listdir(img_folder)
        else:
            log["images"] = []
        print(f"{log['log_id']} | {log['timestamp']} | {log['user']} | {log['step']} | {log['notes']}")
        if log["images"]:
            print(f"   Images: {', '.join(log['images'])}")

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
        print("1. New Client")
        print("2. List Clients")
        print("3. New Project")
        print("4. List Projects")
        print("5. Add Execution Log")
        print("6. View Logs")
        print("7. Exit")
        choice = input("> ").strip()
        if choice == "1": new_client(config, clients)
        elif choice == "2": list_clients(clients)
        elif choice == "3": new_project(config, clients, projects)
        elif choice == "4": list_projects(projects)
        elif choice == "5": add_log(config, projects, recents)
        elif choice == "6": view_logs(projects)
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
