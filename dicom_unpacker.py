import os, subprocess, json

PROJECTS_FILE = "projects.json"
SEVEN_ZIP_EXE = r"C:\Program Files\7-Zip\7z.exe"   # adjust if needed
DEFAULT_DOWNLOADS = r"C:\Users\Lucas\Downloads"    # adjust if needed

def load_projects():
    with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def pick_project(projects):
    pids = list(projects.keys())
    for i, pid in enumerate(pids, 1):
        print(f"{i}. {pid} (Client: {projects[pid]['client_id']})")
    choice = input("Choose project number: ").strip()
    return projects[pids[int(choice)-1]]

def pick_archive(default_dir=DEFAULT_DOWNLOADS):
    print("\nDo you want to drag and drop a DICOM archive, or pick from Downloads?")
    print("[1] Drag and drop")
    print("[2] Pick from Downloads folder")
    method = input("> ").strip()

    if method == "1":
        path = input("Drag & drop your archive here: ").strip('" ')
        return path if os.path.exists(path) else None
    elif method == "2":
        files = [f for f in os.listdir(default_dir) if f.lower().endswith(('.zip', '.rar', '.7z'))]
        for i, fname in enumerate(files, 1):
            print(f"{i}. {fname}")
        sel = int(input("Pick number: "))
        return os.path.join(default_dir, files[sel-1])
    else:
        return None

def extract_archive(archive_path, out_folder):
    os.makedirs(out_folder, exist_ok=True)
    cmd = [SEVEN_ZIP_EXE, "x", "-y", f"-o{out_folder}", archive_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[✓] Extracted {archive_path} → {out_folder}")
    else:
        print(f"[!] Error: {result.stderr}")

def main():
    projects = load_projects()
    project = pick_project(projects)
    dicom_folder = os.path.join(project["path"], "DICOM")

    archive = pick_archive()
    if not archive:
        print("No archive selected.")
        return

    extract_archive(archive, dicom_folder)

if __name__ == "__main__":
    main()
