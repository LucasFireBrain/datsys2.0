import bpy
import os

# ==================================================
# BUTTON 1 — Set Case ID from .blend filename
# ==================================================

class OBJECT_OT_set_bridge_case_id(bpy.types.Operator):
    bl_idname = "object.set_bridge_case_id"
    bl_label = "Set Bridge Case ID"

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Save the .blend file first")
            return {'CANCELLED'}

        txt = bpy.data.objects.get("ID_BRIDGE_TEXT")
        if not txt or txt.type != 'FONT':
            self.report({'ERROR'}, "ID_BRIDGE_TEXT not found")
            return {'CANCELLED'}

        case_id = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
        txt.data.body = case_id
        return {'FINISHED'}


# ==================================================
# BUTTON 2 — Generate Bridge Mesh (Step 1)
# ==================================================

class OBJECT_OT_generate_id_bridge_step1(bpy.types.Operator):
    bl_idname = "object.generate_id_bridge_step1"
    bl_label = "Generate ID Bridge (Mesh)"

    def execute(self, context):

        curve = bpy.data.objects.get("ID_BRIDGE_CURVE")
        text  = bpy.data.objects.get("ID_BRIDGE_TEXT")

        if not curve or not text:
            self.report({'ERROR'}, "Bridge prefabs missing")
            return {'CANCELLED'}

        # Duplicate curve
        curve_dup = curve.copy()
        curve_dup.data = curve.data.copy()
        curve_dup.name = "ID_BRIDGE_CURVE_GEN"
        context.collection.objects.link(curve_dup)

        # Duplicate text
        text_dup = text.copy()
        text_dup.data = text.data.copy()
        text_dup.name = "ID_BRIDGE_TEXT_GEN"
        context.collection.objects.link(text_dup)

        # Convert to mesh + merge
        bpy.ops.object.select_all(action='DESELECT')
        curve_dup.select_set(True)
        text_dup.select_set(True)
        context.view_layer.objects.active = curve_dup

        bpy.ops.object.convert(target='MESH')

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Hide prefabs
        curve.hide_set(True)
        text.hide_set(True)

        return {'FINISHED'}


# ==================================================
# BUTTON 3 — Add Boolean (FAST, not applied)
# ==================================================

class OBJECT_OT_add_bridge_boolean(bpy.types.Operator):
    bl_idname = "object.add_bridge_boolean"
    bl_label = "Add Boolean (FAST)"

    def execute(self, context):

        bridge = bpy.data.objects.get("ID_BRIDGE_CURVE_GEN")
        target = context.scene.idbridge_bool_target

        if not bridge or not target:
            self.report({'ERROR'}, "Bridge mesh or target missing")
            return {'CANCELLED'}

        mod = bridge.modifiers.new(name="BridgeBool", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = target
        mod.solver = 'FAST'

        return {'FINISHED'}


# ==================================================
# BUTTON 4 — Apply Boolean + Prep Cleanup
# ==================================================

class OBJECT_OT_apply_bridge_boolean(bpy.types.Operator):
    bl_idname = "object.apply_bridge_boolean"
    bl_label = "Apply Boolean + Cleanup"

    def execute(self, context):

        bridge = bpy.data.objects.get("ID_BRIDGE_CURVE_GEN")
        if not bridge:
            self.report({'ERROR'}, "Bridge mesh missing")
            return {'CANCELLED'}

        context.view_layer.objects.active = bridge

        for mod in bridge.modifiers:
            if mod.type == 'BOOLEAN':
                bpy.ops.object.modifier_apply(modifier=mod.name)
                break

        # Enter edit mode for manual island cleanup
        bpy.ops.object.mode_set(mode='EDIT')
        self.report({'INFO'}, "Select main island, Ctrl+L, invert, delete")

        return {'FINISHED'}

# ==================================================
# BUTTON 5 — Add Bridge + Text UNION to BM
# ==================================================

class OBJECT_OT_union_bridge_to_bm(bpy.types.Operator):
    bl_idname = "object.union_bridge_to_bm"
    bl_label = "Union Bridge to BM (FAST)"

    def execute(self, context):

        bm = context.scene.idbridge_bool_target
        bridge = bpy.data.objects.get("ID_BRIDGE_CURVE_GEN")
        text = bpy.data.objects.get("ID_BRIDGE_TEXT_GEN")

        if not bm or not bridge or not text:
            self.report({'ERROR'}, "BM, bridge, or text missing")
            return {'CANCELLED'}

        # Union bridge
        mod1 = bm.modifiers.new(name="Union_Bridge", type='BOOLEAN')
        mod1.operation = 'UNION'
        mod1.object = bridge
        mod1.solver = 'FAST'

        # Union text
        mod2 = bm.modifiers.new(name="Union_Text", type='BOOLEAN')
        mod2.operation = 'UNION'
        mod2.object = text
        mod2.solver = 'FAST'

        return {'FINISHED'}

# ==================================================
# UI PANEL
# ==================================================

class VIEW3D_PT_id_bridge(bpy.types.Panel):
    bl_label = "ID Bridge"
    bl_idname = "VIEW3D_PT_id_bridge"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PEEKMacros"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.set_bridge_case_id")
        layout.operator("object.generate_id_bridge_step1")

        layout.separator()
        layout.prop(context.scene, "idbridge_bool_target")
        layout.operator("object.add_bridge_boolean")
        layout.operator("object.apply_bridge_boolean")
        
        layout.separator()
        layout.operator("object.union_bridge_to_bm")


# ==================================================
# REGISTRATION
# ==================================================

def register():
    bpy.utils.register_class(OBJECT_OT_set_bridge_case_id)
    bpy.utils.register_class(OBJECT_OT_generate_id_bridge_step1)
    bpy.utils.register_class(OBJECT_OT_add_bridge_boolean)
    bpy.utils.register_class(OBJECT_OT_apply_bridge_boolean)
    bpy.utils.register_class(OBJECT_OT_union_bridge_to_bm)
    bpy.utils.register_class(VIEW3D_PT_id_bridge)

    bpy.types.Scene.idbridge_bool_target = bpy.props.PointerProperty(
        name="Boolean Target",
        type=bpy.types.Object
    )

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_set_bridge_case_id)
    bpy.utils.unregister_class(OBJECT_OT_generate_id_bridge_step1)
    bpy.utils.unregister_class(OBJECT_OT_add_bridge_boolean)
    bpy.utils.unregister_class(OBJECT_OT_apply_bridge_boolean)
    bpy.utils.unregister_class(OBJECT_OT_union_bridge_to_bm)
    bpy.utils.unregister_class(VIEW3D_PT_id_bridge)


    del bpy.types.Scene.idbridge_bool_target


if __name__ == "__main__":
    register()
