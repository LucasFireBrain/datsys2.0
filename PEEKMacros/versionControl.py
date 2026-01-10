import bpy
import re
import os
from datetime import datetime

# -------------------------------------------------
# Utilities
# -------------------------------------------------

VERSION_REGEX = re.compile(r"^(?P<prefix>.*?)(?P<ver>[A-Z])\.(?P<num>\d{3})$")

def parse_version(name):
    """
    Parses names like A.001, Skull_A.003, etc.
    Returns (base_name, letter, number) or None
    """
    m = VERSION_REGEX.match(name)
    if not m:
        return None
    return m.group("prefix"), m.group("ver"), int(m.group("num"))

def next_version_name(name):
    parsed = parse_version(name)
    if not parsed:
        raise ValueError("Object name does not match version pattern (A.001)")
    prefix, letter, num = parsed
    return f"{prefix}{letter}.{num+1:03d}"

# -------------------------------------------------
# Case / Log helpers
# -------------------------------------------------

def get_blend_dir():
    if not bpy.data.filepath:
        return None
    return os.path.dirname(bpy.data.filepath)

def get_case_root():
    blend_dir = get_blend_dir()
    if not blend_dir:
        return None
    return os.path.dirname(blend_dir)

def append_to_project_log(event, msg, user=""):
    root = get_case_root()
    if not root:
        return False

    log_path = os.path.join(root, "LOG.txt")
    if not os.path.exists(log_path):
        return False

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts} | {event} | {msg}"
    if user:
        line += f" | by {user}"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return True

def get_user(context):
    return getattr(context.scene, "case_user", "").strip()

# -------------------------------------------------
# Operator
# -------------------------------------------------

class OBJECT_OT_new_geometry_version(bpy.types.Operator):
    bl_idname = "object.new_geometry_version"
    bl_label = "New Version (Duplicate & Sculpt)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        original_mode = obj.mode
        old_name = obj.name

        # Exit sculpt mode safely
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        try:
            new_name = next_version_name(old_name)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        # Duplicate object
        bpy.ops.object.duplicate()
        new_obj = context.active_object

        # Ensure unique mesh data
        new_obj.data = new_obj.data.copy()

        # Rename
        new_obj.name = new_name
        new_obj.data.name = new_name

        # Hide previous version
        obj.hide_set(True)
        obj.hide_render = True

        # Ensure selection state
        bpy.ops.object.select_all(action='DESELECT')
        new_obj.select_set(True)
        context.view_layer.objects.active = new_obj

        # Return to sculpt mode if needed
        if original_mode == 'SCULPT':
            bpy.ops.object.mode_set(mode='SCULPT')

        # ---- LOG EVENT ----
        user = get_user(context)
        append_to_project_log(
            "VERSION",
            f"Branched {old_name} → {new_name}",
            user
        )

        self.report({'INFO'}, f"Created new version: {new_name}")
        return {'FINISHED'}

# -------------------------------------------------
# UI Panel
# -------------------------------------------------

class VIEW3D_PT_version_tools(bpy.types.Panel):
    bl_label = "Version Control"
    bl_idname = "VIEW3D_PT_version_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PEEKMacros"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "object.new_geometry_version",
            icon='DUPLICATE'
        )

# -------------------------------------------------
# Registration
# -------------------------------------------------

classes = (
    OBJECT_OT_new_geometry_version,
    VIEW3D_PT_version_tools,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
