import bpy
import os
import json
import subprocess
from datetime import datetime

DATSYS_ROOT = r"C:\Users\Lucas\Desktop\Hexamod\Clients\Hexamod\Datsys"
PEEK_CASE_FILE = "peekCase.json"
LOG_FILE = "LOG.txt"

# ==================================================
# PATH HELPERS
# ==================================================

def get_blend_dir():
    if not bpy.data.filepath:
        return None
    return os.path.dirname(bpy.data.filepath)

def get_case_root():
    blend_dir = get_blend_dir()
    if not blend_dir:
        return None
    return os.path.dirname(blend_dir)

def get_peek_case_path():
    root = get_case_root()
    if not root:
        return None
    return os.path.join(root, PEEK_CASE_FILE)

def get_log_path():
    root = get_case_root()
    if not root:
        return None
    return os.path.join(root, LOG_FILE)

def ensure_log_exists():
    path = get_log_path()
    if not path:
        return None
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("LOG.txt\n\n")
    return path

# ==================================================
# LOGGING
# ==================================================

def append_log(event, message, user=""):
    path = ensure_log_exists()
    if not path:
        return False, "Save the .blend file first"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    user = user.strip() if user.strip() else "UNKNOWN"

    line = f"{ts} | {event} | {message} | by {user}\n"

    with open(path, "a", encoding="utf-8") as f:
        f.write(line)

    return True, None

# ==================================================
# PEEK CASE IO
# ==================================================

def load_peek_case():
    path = get_peek_case_path()
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_peek_case(data):
    path = get_peek_case_path()
    if not path:
        return False, "Save the .blend file first"

    data["actualizado_en"] = datetime.now().isoformat()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True, None

# ==================================================
# OPERATORS
# ==================================================

class OBJECT_OT_reload_peek_case(bpy.types.Operator):
    bl_idname = "object.reload_peek_case"
    bl_label = "Reload PEEK Case"

    def execute(self, context):
        data = load_peek_case()
        scn = context.scene

        for k in PEEK_FIELDS:
            setattr(scn, k, data.get(k, ""))

        self.report({'INFO'}, "PEEK case loaded")
        return {'FINISHED'}


class OBJECT_OT_save_peek_case(bpy.types.Operator):
    bl_idname = "object.save_peek_case"
    bl_label = "Save PEEK Case"

    def execute(self, context):
        scn = context.scene
        data = load_peek_case()

        for k in PEEK_FIELDS:
            data[k] = getattr(scn, k)

        ok, err = save_peek_case(data)
        if not ok:
            self.report({'ERROR'}, err)
            return {'CANCELLED'}

        append_log(
            "PEEK",
            "PEEK case fields updated",
            scn.case_user
        )

        self.report({'INFO'}, "PEEK case saved")
        return {'FINISHED'}


class OBJECT_OT_open_case_folder(bpy.types.Operator):
    bl_idname = "object.open_case_folder"
    bl_label = "Open Case Folder"

    def execute(self, context):
        root = get_case_root()
        if not root:
            self.report({'ERROR'}, "Save the .blend file first")
            return {'CANCELLED'}

        subprocess.Popen(f'explorer "{root}"')
        return {'FINISHED'}


class OBJECT_OT_export_selected_stl(bpy.types.Operator):
    bl_idname = "object.export_selected_stl"
    bl_label = "Export Selected STL"

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Save the .blend file first")
            return {'CANCELLED'}

        if not context.selected_objects:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}

        active = context.active_object
        out_dir = get_blend_dir()
        filename = f"{active.name}.stl"
        out_path = os.path.join(out_dir, filename)

        bpy.ops.wm.stl_export(
            filepath=out_path,
            export_selected_objects=True,
            apply_modifiers=True,
            global_scale=1.0
        )

        append_log(
            "EXPORT",
            f"STL exported: {filename}",
            context.scene.case_user
        )

        self.report({'INFO'}, "STL exported")
        return {'FINISHED'}

# ==================================================
# UI PANEL
# ==================================================

PEEK_FIELDS = [
    "nombre_doctor",
    "hospital_clinica",
    "nombre_paciente",
    "fecha_cirugia",
    "fecha_entrega_estimada",
    "region",
    "especificaciones",
    "precio_clp",
]

class VIEW3D_PT_peek_case(bpy.types.Panel):
    bl_label = "PEEK Case"
    bl_idname = "VIEW3D_PT_peek_case"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PEEKMacros"

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        layout.prop(scn, "case_user", text="User")

        layout.separator()
        layout.operator("object.reload_peek_case", icon='FILE_REFRESH')

        for k in PEEK_FIELDS:
            layout.prop(scn, k, text=k.replace("_", " ").title())

        layout.separator()
        layout.operator("object.save_peek_case", icon='FILE_TICK')

        layout.separator()
        layout.operator("object.open_case_folder", icon='FILE_FOLDER')
        layout.operator("object.export_selected_stl", icon='EXPORT')

# ==================================================
# REGISTRATION
# ==================================================

def register():
    bpy.utils.register_class(OBJECT_OT_reload_peek_case)
    bpy.utils.register_class(OBJECT_OT_save_peek_case)
    bpy.utils.register_class(OBJECT_OT_open_case_folder)
    bpy.utils.register_class(OBJECT_OT_export_selected_stl)
    bpy.utils.register_class(VIEW3D_PT_peek_case)

    bpy.types.Scene.case_user = bpy.props.StringProperty(
        name="User",
        description="Operator ID / initials",
        default="",
        maxlen=50
    )

    for k in PEEK_FIELDS:
        setattr(
            bpy.types.Scene,
            k,
            bpy.props.StringProperty(name=k)
        )

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_reload_peek_case)
    bpy.utils.unregister_class(OBJECT_OT_save_peek_case)
    bpy.utils.unregister_class(OBJECT_OT_open_case_folder)
    bpy.utils.unregister_class(OBJECT_OT_export_selected_stl)
    bpy.utils.unregister_class(VIEW3D_PT_peek_case)

    del bpy.types.Scene.case_user

    for k in PEEK_FIELDS:
        delattr(bpy.types.Scene, k)

if __name__ == "__main__":
    register()
