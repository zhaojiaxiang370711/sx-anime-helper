# Paper said：ciallo
import bpy
from bpy.types import Panel

class PAPERZHU_PT_material(Panel):
    bl_label = "Paper朱 高光皮肤材质"
    bl_idname = "PAPERZHU_PT_material"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.type == 'MESH' and obj.active_material is not None

    def draw(self, context):
        layout = self.layout
        s = context.scene.paperzhu_settings
        layout.prop(s, "toon_mix", slider=True)
        layout.operator("paperzhu.skin_active", icon='NODE_MATERIAL')

CLASSES = (PAPERZHU_PT_material,)

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
