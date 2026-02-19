# Paper said：ciallo
import bpy
from bpy.types import Operator
from .ops_skin import apply_highlight_skin
from .constants import OUTLINE_MATERIAL_NAME
from .utils_engine import ensure_eevee

class PAPERZHU_OT_apply_skin_slot(Operator):
    bl_idname = "paperzhu.skin_slot"
    bl_label = "仅处理所选材质槽"
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):
        ensure_eevee(context)
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "请先选择网格对象")
            return {'CANCELLED'}

        s = context.scene.paperzhu_settings
        if s.target_slot == "":
            self.report({'ERROR'}, "请先选择目标材质槽")
            return {'CANCELLED'}

        idx = int(s.target_slot)
        if idx >= len(obj.material_slots):
            self.report({'ERROR'}, "材质槽索引无效")
            return {'CANCELLED'}

        mat = obj.material_slots[idx].material
        if mat and mat.name == OUTLINE_MATERIAL_NAME:
            self.report({'ERROR'}, f"不允许处理描边材质：{OUTLINE_MATERIAL_NAME}")
            return {'CANCELLED'}

        if apply_highlight_skin(mat, s.toon_mix):
            self.report({'INFO'}, f"材质槽 {idx} 已添加高光皮肤材质")
            return {'FINISHED'}

        self.report({'WARNING'}, "当前材质无法处理")
        return {'CANCELLED'}

CLASSES = (PAPERZHU_OT_apply_skin_slot,)

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
