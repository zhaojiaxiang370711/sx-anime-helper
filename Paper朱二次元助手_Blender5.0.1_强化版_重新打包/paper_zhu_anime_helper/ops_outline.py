# Paper said：ciallo
import bpy
from bpy.types import Operator
from .utils_engine import ensure_eevee
from .materials import ensure_outline_material
from .constants import OUTLINE_MODIFIER_NAME, OUTLINE_MATERIAL_NAME

class PAPERZHU_OT_outline(Operator):
    bl_idname = "paperzhu.outline"
    bl_label = "一键添加黑色描边"
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):
        ensure_eevee(context)
        mat = ensure_outline_material()

        for ob in context.selected_objects:
            if ob.type != 'MESH':
                continue

            names = [m.name for m in ob.data.materials if m]
            if OUTLINE_MATERIAL_NAME not in names:
                ob.data.materials.append(mat)

            mod = ob.modifiers.get(OUTLINE_MODIFIER_NAME)
            if not mod:
                mod = ob.modifiers.new(OUTLINE_MODIFIER_NAME, 'SOLIDIFY')

            mod.thickness = 0.001
            mod.offset = 0
            mod.material_offset = max(0, len(ob.material_slots)-1)
            mod.use_even_offset = False
            mod.use_rim = False
            if hasattr(mod, "use_flip_normals"):
                mod.use_flip_normals = True

        return {'FINISHED'}

CLASSES = (PAPERZHU_OT_outline,)

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
