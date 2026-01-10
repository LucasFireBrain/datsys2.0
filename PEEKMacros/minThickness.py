import bpy
import bmesh
from mathutils.bvhtree import BVHTree

# ==================================================
# SCENE PROPERTIES (N-panel controls)
# ==================================================

def register_props():
    s = bpy.types.Scene

    s.thick_bone_object = bpy.props.PointerProperty(
        name="Bone Object",
        type=bpy.types.Object,
        description="Bone mesh used for thickness raycasts"
    )

    s.thick_min = bpy.props.FloatProperty(
        name="Min Thickness",
        default=2.0,
        min=0.0
    )

    s.thick_strength = bpy.props.FloatProperty(
        name="Strength",
        default=1.0,
        min=0.0
    )

    s.thick_max_push = bpy.props.FloatProperty(
        name="Max Push",
        default=5.0,
        min=0.0
    )

    s.thick_min_incidence = bpy.props.FloatProperty(
        name="Min Incidence",
        description="0 = allow tangents, 1 = only perpendicular",
        default=0.3,
        min=0.0,
        max=1.0
    )

    s.thick_incidence_falloff = bpy.props.FloatProperty(
        name="Incidence Falloff",
        description="Soft fade near tangential hits",
        default=0.5,
        min=0.01
    )

def unregister_props():
    s = bpy.types.Scene
    del s.thick_bone_object
    del s.thick_min
    del s.thick_strength
    del s.thick_max_push
    del s.thick_min_incidence
    del s.thick_incidence_falloff

# ==================================================
# OPERATOR
# ==================================================

class OBJECT_OT_fix_thin_regions(bpy.types.Operator):
    bl_idname = "object.fix_thin_regions"
    bl_label = "Fix Thin Regions (Bone Masked)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        implant = context.active_object
        bone = scene.thick_bone_object

        if not implant or implant.type != 'MESH':
            self.report({'ERROR'}, "Active object must be the implant mesh")
            return {'CANCELLED'}

        if not bone or bone.type != 'MESH':
            self.report({'ERROR'}, "Please select a bone mesh")
            return {'CANCELLED'}

        # ------------------------------------------
        # Duplicate implant safely (data API)
        # ------------------------------------------
        obj = implant.copy()
        obj.data = implant.data.copy()
        obj.name = f"{implant.name}_THICK"
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj

        # Ensure Object Mode
        original_mode = obj.mode
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data

        # ------------------------------------------
        # Build bmesh
        # ------------------------------------------
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.normal_update()

        # ------------------------------------------
        # Build BVH from BONE ONLY
        # ------------------------------------------
        depsgraph = context.evaluated_depsgraph_get()
        bvh_bone = BVHTree.FromObject(bone, depsgraph)

        mw = obj.matrix_world
        moved = 0

        # ------------------------------------------
        # Core algorithm
        # ------------------------------------------
        for v in bm.verts:
            if not v.is_valid:
                continue

            n_local = v.normal.normalized()
            n_world = (mw.to_3x3() @ n_local).normalized()
            origin = mw @ v.co

            # ----------------------------------
            # Exterior ray: is vertex facing bone?
            # ----------------------------------
            exterior_hit = bvh_bone.ray_cast(
                origin + n_world * 0.001,
                n_world
            )

            if exterior_hit[0] is not None:
                continue  # vertex faces bone → do not move

            # ----------------------------------
            # Interior ray: thickness measurement
            # ----------------------------------
            ray_dir = -n_world
            interior_hit = bvh_bone.ray_cast(
                origin + ray_dir * 0.001,
                ray_dir
            )

            if interior_hit[0] is None:
                continue  # no bone behind → skip

            hit_normal = interior_hit[1]
            inward_dist = interior_hit[3]

            if inward_dist >= scene.thick_min:
                continue

            # ----------------------------------
            # Incidence quality (angle check)
            # ----------------------------------
            incidence = abs(ray_dir.dot(hit_normal))

            if incidence < scene.thick_min_incidence:
                continue

            incidence_factor = (
                (incidence - scene.thick_min_incidence)
                / scene.thick_incidence_falloff
            )
            incidence_factor = max(0.0, min(1.0, incidence_factor))

            # ----------------------------------
            # Safe outward direction (bone-aware)
            # ----------------------------------
            safe_dir_world = -ray_dir  # always away from bone

            # ----------------------------------
            # Compute displacement
            # ----------------------------------
            delta = (scene.thick_min - inward_dist)
            delta *= scene.thick_strength
            delta *= incidence_factor
            delta = min(delta, scene.thick_max_push)

            if delta <= 0.0:
                continue

            safe_dir_local = (mw.inverted().to_3x3() @ safe_dir_world).normalized()
            v.co += safe_dir_local * delta
            moved += 1

        # ------------------------------------------
        # Write back
        # ------------------------------------------
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()

        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=original_mode)

        self.report({'INFO'}, f"Thickened {moved} vertices")
        return {'FINISHED'}

# ==================================================
# UI PANEL
# ==================================================

class VIEW3D_PT_thickness_tools(bpy.types.Panel):
    bl_label = "Thickness Tools"
    bl_idname = "VIEW3D_PT_thickness_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PEEKMacros"

    def draw(self, context):
        layout = self.layout
        s = context.scene

        layout.prop(s, "thick_bone_object")
        layout.separator()
        layout.prop(s, "thick_min")
        layout.prop(s, "thick_strength")
        layout.prop(s, "thick_max_push")
        layout.separator()
        layout.prop(s, "thick_min_incidence")
        layout.prop(s, "thick_incidence_falloff")
        layout.separator()
        layout.operator("object.fix_thin_regions", icon='MOD_SOLIDIFY')

# ==================================================
# REGISTRATION
# ==================================================

classes = (
    OBJECT_OT_fix_thin_regions,
    VIEW3D_PT_thickness_tools,
)

def register():
    register_props()
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    unregister_props()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
