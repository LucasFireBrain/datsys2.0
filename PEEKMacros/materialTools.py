import bpy
import re

# ----------------------------
# RULES (order matters)
# ----------------------------

RULES = [
    (r"(skull|mandible|maxilla)", "Bone"),
    (r"(skin|soft|tissue)", "Skin"),
    (r"(plates)", "Plates"),
    (r"teeth", "Teeth"),
    (r"canal", "Canal"),
    (r"\bA\.\d+", "A"),
    (r"\bB\.\d+", "B"),
    (r"\bC\.\d+", "C"),
]

# Materials that get transparency sliders
TRANSPARENCY_MATERIALS = [
    "Bone",
    "A",
    "B",
    "Skin",
    "Plates"
]

# ----------------------------
# OPERATOR: Assign materials
# ----------------------------

class OBJECT_OT_assign_materials_selected(bpy.types.Operator):
    bl_idname = "object.assign_materials_selected"
    bl_label = "Assign Materials (Selected)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mats = bpy.data.materials

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            name = obj.name.lower()

            for pattern, mat_name in RULES:
                if re.search(pattern, name, re.IGNORECASE):
                    mat = mats.get(mat_name)
                    if not mat:
                        self.report({'WARNING'}, f"Material '{mat_name}' not found")
                        break

                    if not obj.data.materials:
                        obj.data.materials.append(mat)
                    else:
                        obj.data.materials[0] = mat

                    break  # first match wins

        return {'FINISHED'}


# ----------------------------
# Transparency properties
# ----------------------------

def update_viewport_alpha(self, context):
    mat = bpy.data.materials.get(self.name)
    if not mat:
        return

    col = list(mat.diffuse_color)
    col[3] = self.alpha
    mat.diffuse_color = col


class MaterialAlphaItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    alpha: bpy.props.FloatProperty(
        name="",
        min=0.0,
        max=1.0,
        default=1.0,
        update=update_viewport_alpha
    )


# ----------------------------
# UI PANEL
# ----------------------------

class VIEW3D_PT_material_assign(bpy.types.Panel):
    bl_label = "Material Tools"
    bl_idname = "VIEW3D_PT_material_assign"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PEEKMacros"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator(
            "object.assign_materials_selected",
            icon='MATERIAL'
        )

        layout.separator()
        layout.label(text="Viewport Transparency")

        for item in scene.material_alpha_items:
            row = layout.row()
            row.prop(item, "alpha", slider=True, text=item.name)


# ----------------------------
# REGISTRATION
# ----------------------------

classes = (
    OBJECT_OT_assign_materials_selected,
    MaterialAlphaItem,
    VIEW3D_PT_material_assign,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.material_alpha_items = bpy.props.CollectionProperty(
        type=MaterialAlphaItem
    )

    scene = bpy.context.scene
    scene.material_alpha_items.clear()

    for name in TRANSPARENCY_MATERIALS:
        item = scene.material_alpha_items.add()
        item.name = name
        item.alpha = 1.0


def unregister():
    del bpy.types.Scene.material_alpha_items

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
