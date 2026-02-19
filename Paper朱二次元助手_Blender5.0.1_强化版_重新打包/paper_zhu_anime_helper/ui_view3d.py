# Paper said：ciallo
import bpy
from bpy.types import Panel

class PAPERZHU_PT_view3d(Panel):
    bl_label = "Paper二分助手"
    bl_idname = "PAPERZHU_PT_view3d"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Paper二分"

    def draw(self, context):
        layout = self.layout
        s = context.scene.paperzhu_settings
        layout.operator("paperzhu.outline", icon='MOD_SOLIDIFY')
        layout.operator("paperzhu.color", icon='COLOR')
        layout.separator()
        layout.prop(s, "toon_mix", slider=True)
        layout.operator("paperzhu.skin_all", icon='MATERIAL')

CLASSES = (PAPERZHU_PT_view3d,)

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
