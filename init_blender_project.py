# init_blender_project.py
# Runs automatically when Blender starts
# Blender 4.x compatible

import bpy
import sys
import os

# ----------------------------
# Helpers
# ----------------------------
def log(msg):
    print(msg)

# ----------------------------
# Read args
# ----------------------------
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []

if not argv:
    log("[BLENDER] No Segmentations directory provided.")
    seg_dir = None
else:
    seg_dir = argv[0]

log(f"[BLENDER] Segmentations arg: {seg_dir}")

if not seg_dir or not os.path.isdir(seg_dir):
    log("[BLENDER] Segmentations folder not found. Skipping import.")
    seg_dir = None

# ----------------------------
# Ensure collection
# ----------------------------
COLLECTION_NAME = "Segmentations"

scene = bpy.context.scene
collection = bpy.data.collections.get(COLLECTION_NAME)

if not collection:
    collection = bpy.data.collections.new(COLLECTION_NAME)
    scene.collection.children.link(collection)
    log(f"[BLENDER] Created collection: {COLLECTION_NAME}")
else:
    log(f"[BLENDER] Using existing collection: {COLLECTION_NAME}")

# ----------------------------
# Import STLs (batch, Blender 4.x)
# ----------------------------
imported = []

if seg_dir:
    files = [
        {"name": fn}
        for fn in sorted(os.listdir(seg_dir))
        if fn.lower().endswith(".stl")
    ]

    if not files:
        log("[BLENDER] No STL files found in Segmentations.")
    else:
        log(f"[BLENDER] Importing {len(files)} STL files...")
        bpy.ops.wm.stl_import(
            directory=seg_dir,
            files=files
        )

        imported = list(bpy.context.selected_objects)

        for obj in imported:
            if obj.name not in collection.objects:
                collection.objects.link(obj)

            try:
                scene.collection.objects.unlink(obj)
            except Exception:
                pass

        log(f"[BLENDER] Imported {len(imported)} objects.")

# ----------------------------
# Frame view
# ----------------------------
if imported:
    bpy.ops.object.select_all(action="DESELECT")
    for o in imported:
        o.select_set(True)

    bpy.context.view_layer.objects.active = imported[0]

    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            with bpy.context.temp_override(area=area):
                bpy.ops.view3d.view_selected()
            break

# ----------------------------
# Save file
# ----------------------------
try:
    bpy.ops.wm.save_mainfile()
    log("[BLENDER] File saved.")
except Exception as e:
    log(f"[BLENDER] Save failed: {e}")

# ----------------------------
# Keep Blender alive indefinitely
# ----------------------------
def keep_alive():
    return 5.0  # seconds

bpy.app.timers.register(keep_alive)
log("[BLENDER] Initialization complete. Control handed to user.")
