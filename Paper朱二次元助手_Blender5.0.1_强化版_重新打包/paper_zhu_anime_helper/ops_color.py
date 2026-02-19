# Paper said：ciallo
import bpy
from bpy.types import Operator
from .utils_engine import ensure_eevee

class PAPERZHU_OT_color(Operator):
    bl_idname = "paperzhu.color"
    bl_label = "一键二次元色彩"
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):
        ensure_eevee(context)
        vs = context.scene.view_settings
        vs.view_transform = "Standard"
        vs.look = "Medium High Contrast"
        return {'FINISHED'}

CLASSES = (PAPERZHU_OT_color,)

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
