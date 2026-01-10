import bpy
import os
import subprocess
import sys
from datetime import datetime

# ----------------------------
# CONFIG
# ----------------------------

SNAPSHOT_FOLDER_NAME = "Snapshots"
IMAGE_SIZE = 1080

ORTHO_VIEWS = {
    "Front":  'FRONT',
    "Right":  'RIGHT',
    "Left":   'LEFT',
    "Top":    'TOP',
    "Bottom": 'BOTTOM',
}

# ----------------------------
# UTILS
# ----------------------------

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def get_blend_dir():
    return os.path.dirname(bpy.data.filepath)

def open_folder(path):
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.call(["open", path])
    else:
        subprocess.call(["xdg-open", path])

def force_viewport_redraw():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()
    bpy.context.view_layer.update()

def viewport_render(filepath):
    force_viewport_redraw()
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.opengl(write_still=True, view_context=True)

def align_viewport_to_camera(camera):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            region_3d = space.region_3d

            region_3d.view_rotation = camera.matrix_world.to_quaternion()
            region_3d.view_perspective = 'PERSP'
            space.lens = camera.data.lens

            space.clip_start = camera.data.clip_start
            space.clip_end   = camera.data.clip_end
            space.shading.type = 'SOLID'
            break

def set_axis_ortho(axis):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            region = next(r for r in area.regions if r.type == 'WINDOW')
            space = area.spaces.active

            with bpy.context.temp_override(
                area=area,
                region=region,
                space_data=space,
            ):
                bpy.ops.view3d.view_axis(type=axis)

            space.region_3d.view_perspective = 'ORTHO'
            space.shading.type = 'SOLID'
            break

# ----------------------------
# OVERLAY CONTROL
# ----------------------------

def disable_visual_overlays():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            overlay = area.spaces.active.overlay
            state = {
                "outline": overlay.show_outline_selected,
                "origins": overlay.show_object_origins,
                "cursor":  overlay.show_cursor,
            }

            overlay.show_outline_selected = False
            overlay.show_object_origins = False
            overlay.show_cursor = False

            return state
    return None

def restore_visual_overlays(state):
    if not state:
        return

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            overlay = area.spaces.active.overlay
            overlay.show_outline_selected = state["outline"]
            overlay.show_object_origins = state["origins"]
            overlay.show_cursor = state["cursor"]
            break

def timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# ----------------------------
# PROPERTIES
# ----------------------------

class SNAPSHOT_Properties(bpy.types.PropertyGroup):
    open_dir_on_export: bpy.props.BoolProperty(
        name="Open Dir on Export",
        description="Open snapshot folder after export",
        default=True,
    )

# ----------------------------
# OPERATORS
# ----------------------------

class OBJECT_OT_snapshot_split(bpy.types.Operator):
    bl_idname = "object.snapshot_split"
    bl_label = "Snapshot (Cameras + Ortho)"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Save the .blend file first")
            return {'CANCELLED'}

        active = context.active_object
        version_name = active.name if active else "UNNAMED"

        root = get_blend_dir()
        out_dir = os.path.join(root, SNAPSHOT_FOLDER_NAME, version_name)
        ensure_dir(out_dir)

        scene = context.scene
        scene.render.resolution_x = IMAGE_SIZE
        scene.render.resolution_y = IMAGE_SIZE
        scene.render.resolution_percentage = 100

        overlay_state = disable_visual_overlays()

        cameras = [obj for obj in scene.objects if obj.type == 'CAMERA']
        for cam in cameras:
            if cam.data.type != 'PERSP':
                continue

            align_viewport_to_camera(cam)
            filepath = os.path.join(out_dir, f"{version_name} {cam.name}.png")
            viewport_render(filepath)

        for label, axis in ORTHO_VIEWS.items():
            set_axis_ortho(axis)
            filepath = os.path.join(out_dir, f"{version_name} Ortho {label}.png")
            viewport_render(filepath)

        restore_visual_overlays(overlay_state)

        if scene.snapshot_props.open_dir_on_export:
            open_folder(out_dir)

        self.report({'INFO'}, f"Snapshots saved to {out_dir}")
        return {'FINISHED'}


class OBJECT_OT_snapshot_free_view(bpy.types.Operator):
    bl_idname = "object.snapshot_free_view"
    bl_label = "Snapshot Free View"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Save the .blend file first")
            return {'CANCELLED'}

        active = context.active_object
        version_name = active.name if active else "UNNAMED"

        root = get_blend_dir()
        out_dir = os.path.join(root, SNAPSHOT_FOLDER_NAME, version_name)
        ensure_dir(out_dir)

        scene = context.scene
        scene.render.resolution_x = IMAGE_SIZE
        scene.render.resolution_y = IMAGE_SIZE
        scene.render.resolution_percentage = 100

        overlay_state = disable_visual_overlays()

        fname = f"{version_name} FreeView_{timestamp()}.png"
        filepath = os.path.join(out_dir, fname)
        viewport_render(filepath)

        restore_visual_overlays(overlay_state)

        self.report({'INFO'}, f"Free view saved: {fname}")
        return {'FINISHED'}

# ----------------------------
# UI PANEL
# ----------------------------

class VIEW3D_PT_snapshot_split(bpy.types.Panel):
    bl_label = "Snapshot Tools"
    bl_idname = "VIEW3D_PT_snapshot_split"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PEEKMacros"

    def draw(self, context):
        layout = self.layout
        props = context.scene.snapshot_props

        layout.prop(props, "open_dir_on_export")
        layout.operator("object.snapshot_split", icon='RENDER_STILL')
        layout.separator()
        layout.operator("object.snapshot_free_view", icon='HIDE_OFF')

# ----------------------------
# REGISTRATION
# ----------------------------

classes = (
    SNAPSHOT_Properties,
    OBJECT_OT_snapshot_split,
    OBJECT_OT_snapshot_free_view,
    VIEW3D_PT_snapshot_split,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.snapshot_props = bpy.props.PointerProperty(
        type=SNAPSHOT_Properties
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.snapshot_props

if __name__ == "__main__":
    register()
