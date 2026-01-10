import bpy

# ----------------------------
# OPERATOR
# ----------------------------

class OBJECT_OT_auto_fat_prep(bpy.types.Operator):
    bl_idname = "object.auto_fat_prep"
    bl_label = "AutoFAT Prep"
    bl_description = (
        "Duplicate active mesh, apply modifiers on copy, hide original, "
        "rename to _FAT, enter Edit Mode and select all faces"
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Select one mesh object")
            return {'CANCELLED'}

        # Ensure Object Mode
        bpy.ops.object.mode_set(mode='OBJECT')

        original = obj

        # Duplicate
        bpy.ops.object.duplicate()
        fat_obj = context.active_object

        # Rename duplicate
        fat_obj.name = f"{original.name}_FAT"

        # Apply all modifiers on the duplicate
        for mod in list(fat_obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except RuntimeError:
                # Skip unappliable modifiers safely
                pass

        # Hide original
        original.hide_set(True)

        # Apply scale (important for correct mm behavior)
        bpy.ops.object.transform_apply(
            location=False,
            rotation=False,
            scale=True
        )

        # Enter Edit Mode
        bpy.ops.object.mode_set(mode='EDIT')

        # Face select mode + select all
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')

        return {'FINISHED'}

# ----------------------------
# UI PANEL
# ----------------------------

class VIEW3D_PT_auto_fat_prep(bpy.types.Panel):
    bl_label = "AutoFAT"
    bl_idname = "VIEW3D_PT_auto_fat_prep"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PEEKMacros"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "object.auto_fat_prep",
            icon='DUPLICATE'
        )

# ----------------------------
# REGISTRATION
# ----------------------------

classes = (
    OBJECT_OT_auto_fat_prep,
    VIEW3D_PT_auto_fat_prep,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
