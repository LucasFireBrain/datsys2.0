import bpy

# ----------------------------
# Properties
# ----------------------------

class SELDEC_Properties(bpy.types.PropertyGroup):
    decimate_ratio: bpy.props.FloatProperty(
        name="Decimate Ratio",
        description="Decimate ratio for selected meshes",
        min=0.0,
        max=1.0,
        default=0.35,
    )


# ----------------------------
# Operators
# ----------------------------

class OBJECT_OT_add_decimate_selected(bpy.types.Operator):
    bl_idname = "object.add_decimate_selected"
    bl_label = "Add Decimate (Selected)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ratio = context.scene.seldec_props.decimate_ratio

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # Avoid stacking duplicates
            if "SEL_Decimate" in obj.modifiers:
                continue

            mod = obj.modifiers.new(name="SEL_Decimate", type='DECIMATE')
            mod.ratio = ratio
            mod.use_collapse_triangulate = True

        return {'FINISHED'}


class OBJECT_OT_apply_decimate_selected(bpy.types.Operator):
    bl_idname = "object.apply_decimate_selected"
    bl_label = "Apply Decimate (Selected)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            mod = obj.modifiers.get("SEL_Decimate")
            if not mod:
                continue

            context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=mod.name)

        return {'FINISHED'}


# ----------------------------
# UI Panel
# ----------------------------

class VIEW3D_PT_selection_decimate(bpy.types.Panel):
    bl_label = "Selection Decimate"
    bl_idname = "VIEW3D_PT_selection_decimate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PEEKMacros"

    def draw(self, context):
        layout = self.layout
        props = context.scene.seldec_props

        layout.prop(props, "decimate_ratio")
        layout.separator()
        layout.operator("object.add_decimate_selected", icon='MOD_DECIM')
        layout.operator("object.apply_decimate_selected", icon='CHECKMARK')


# ----------------------------
# Registration
# ----------------------------

classes = (
    SELDEC_Properties,
    OBJECT_OT_add_decimate_selected,
    OBJECT_OT_apply_decimate_selected,
    VIEW3D_PT_selection_decimate,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.seldec_props = bpy.props.PointerProperty(type=SELDEC_Properties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.seldec_props

if __name__ == "__main__":
    register()
