import bpy
import bmesh

# ======================================================
# CORE LOGIC
# ======================================================

def keep_largest_island(obj):
    if obj.type != 'MESH':
        return False, "Active object is not a mesh"

    # Enter Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    visited = set()
    islands = []

    # --- find islands ---
    for face in bm.faces:
        if face in visited:
            continue

        stack = [face]
        island = set()

        while stack:
            f = stack.pop()
            if f in island:
                continue

            island.add(f)
            visited.add(f)

            for e in f.edges:
                for linked in e.link_faces:
                    if linked not in island:
                        stack.append(linked)

        islands.append(island)

    if len(islands) <= 1:
        bpy.ops.object.mode_set(mode='SCULPT')
        return True, "Only one island found"

    # --- keep largest ---
    largest = max(islands, key=len)

    for island in islands:
        if island is largest:
            continue
        for f in island:
            f.select = True

    bpy.ops.mesh.delete(type='FACE')
    bmesh.update_edit_mesh(obj.data)

    bpy.ops.object.mode_set(mode='SCULPT')
    return True, "Kept largest island"


# ======================================================
# OPERATOR
# ======================================================

class OBJECT_OT_islands_keep_largest(bpy.types.Operator):
    bl_idname = "object.islands_keep_largest"
    bl_label = "Keep Largest Island"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        ok, msg = keep_largest_island(obj)
        if not ok:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        self.report({'INFO'}, msg)
        return {'FINISHED'}


# ======================================================
# UI PANEL
# ======================================================

class VIEW3D_PT_islands(bpy.types.Panel):
    bl_label = "Islands"
    bl_idname = "VIEW3D_PT_islands"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PEEKMacros"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "object.islands_keep_largest",
            icon='MESH_GRID'
        )


# ======================================================
# REGISTRATION
# ======================================================

classes = (
    OBJECT_OT_islands_keep_largest,
    VIEW3D_PT_islands,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
