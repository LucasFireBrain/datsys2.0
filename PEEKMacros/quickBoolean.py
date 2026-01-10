import bpy

# ======================================================
# PROPERTIES
# ======================================================

class QB_Properties(bpy.types.PropertyGroup):
    use_collection: bpy.props.PointerProperty(
        name="Collection",
        description="Optional collection to use as boolean source",
        type=bpy.types.Collection
    )

    hide_cutters: bpy.props.BoolProperty(
        name="Hide Cutters",
        description="Hide cutter objects/collection after adding/applying booleans",
        default=False
    )


# ======================================================
# CORE LOGIC
# ======================================================

def get_cutters(context):
    """Return (object_cutters, collection_cutters) based on rules."""
    active = context.active_object
    if not active or active.type != 'MESH':
        return [], None

    # Source 1: selected objects excluding active
    obj_cutters = [
        o for o in context.selected_objects
        if o.type == 'MESH' and o != active
    ]

    # Source 2: optional collection from UI
    col = context.scene.qb_props.use_collection
    col_cutters = col if col else None

    return obj_cutters, col_cutters


def add_boolean(
    target,
    operation,
    solver='FAST',
    obj=None,
    collection=None
):
    """Add one boolean modifier with presets."""
    mod = target.modifiers.new(
        name=f"QB_{operation}",
        type='BOOLEAN'
    )
    mod.operation = operation
    mod.solver = solver

    if obj:
        mod.object = obj
    if collection:
        mod.collection = collection

    return mod


def apply_boolean(mod, target):
    bpy.context.view_layer.objects.active = target
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except RuntimeError:
        pass


def hide_cutters_safe(objects, collection):
    # Safe visibility only (reversible in Outliner)
    for o in objects:
        o.hide_set(True)
    if collection:
        collection.hide_viewport = True


# ======================================================
# OPERATORS
# ======================================================

class OBJECT_OT_qb_add(bpy.types.Operator):
    bl_idname = "object.qb_add"
    bl_label = "Add Booleans (FAST)"
    bl_options = {'REGISTER', 'UNDO'}

    operation: bpy.props.EnumProperty(
        items=[
            ('DIFFERENCE', 'Difference', ''),
            ('UNION', 'Union', ''),
            ('INTERSECT', 'Intersect', '')
        ],
        default='DIFFERENCE'
    )

    def execute(self, context):
        target = context.active_object
        if not target or target.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        obj_cutters, col = get_cutters(context)

        # Source 3: empty preset if no sources
        if not obj_cutters and not col:
            add_boolean(target, self.operation)
            return {'FINISHED'}

        # Source 1: objects
        for o in obj_cutters:
            add_boolean(target, self.operation, obj=o)

        # Source 2: collection
        if col:
            add_boolean(target, self.operation, collection=col)

        if context.scene.qb_props.hide_cutters:
            hide_cutters_safe(obj_cutters, col)

        return {'FINISHED'}


class OBJECT_OT_qb_add_apply(bpy.types.Operator):
    bl_idname = "object.qb_add_apply"
    bl_label = "Add + Apply"
    bl_options = {'REGISTER', 'UNDO'}

    operation: bpy.props.EnumProperty(
        items=[
            ('DIFFERENCE', 'Difference', ''),
            ('UNION', 'Union', ''),
            ('INTERSECT', 'Intersect', '')
        ],
        default='DIFFERENCE'
    )

    def execute(self, context):
        target = context.active_object
        if not target or target.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        obj_cutters, col = get_cutters(context)
        created = []

        if not obj_cutters and not col:
            mod = add_boolean(target, self.operation)
            apply_boolean(mod, target)
            return {'FINISHED'}

        for o in obj_cutters:
            created.append(add_boolean(target, self.operation, obj=o))

        if col:
            created.append(add_boolean(target, self.operation, collection=col))

        for m in created:
            apply_boolean(m, target)

        if context.scene.qb_props.hide_cutters:
            hide_cutters_safe(obj_cutters, col)

        return {'FINISHED'}


class OBJECT_OT_qb_apply_all(bpy.types.Operator):
    bl_idname = "object.qb_apply_all"
    bl_label = "Apply All Booleans"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.active_object
        if not target or target.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        for mod in list(target.modifiers):
            if mod.type == 'BOOLEAN':
                apply_boolean(mod, target)

        return {'FINISHED'}


# ======================================================
# UI PANEL
# ======================================================

class VIEW3D_PT_quick_boolean(bpy.types.Panel):
    bl_label = "Quick Boolean"
    bl_idname = "VIEW3D_PT_quick_boolean"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PEEKMacros"

    def draw(self, context):
        layout = self.layout
        props = context.scene.qb_props

        layout.prop(props, "use_collection")
        layout.prop(props, "hide_cutters")

        col = layout.column(align=True)
        col.label(text="Add")
        col.operator("object.qb_add", text="Diff (FAST)").operation = 'DIFFERENCE'
        col.operator("object.qb_add", text="Union (FAST)").operation = 'UNION'
        col.operator("object.qb_add", text="Intersect (FAST)").operation = 'INTERSECT'

        col = layout.column(align=True)
        col.label(text="Add + Apply")
        col.operator("object.qb_add_apply", text="Diff + Apply").operation = 'DIFFERENCE'
        col.operator("object.qb_add_apply", text="Union + Apply").operation = 'UNION'
        col.operator("object.qb_add_apply", text="Intersect + Apply").operation = 'INTERSECT'

        layout.separator()
        layout.operator("object.qb_apply_all", icon='CHECKMARK')


# ======================================================
# REGISTRATION
# ======================================================

classes = (
    QB_Properties,
    OBJECT_OT_qb_add,
    OBJECT_OT_qb_add_apply,
    OBJECT_OT_qb_apply_all,
    VIEW3D_PT_quick_boolean,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.qb_props = bpy.props.PointerProperty(type=QB_Properties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.qb_props

if __name__ == "__main__":
    register()
