# Paper said：ciallo
import bpy
from bpy.types import Panel

class PAPERZHU_PT_shader(Panel):
    bl_label = "Paper二分助手"
    bl_idname = "PAPERZHU_PT_shader"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Paper二分"

    @classmethod
    def poll(cls, context):
        return context.space_data and getattr(context.space_data, "tree_type", "") == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout
        s = context.scene.paperzhu_settings
        layout.prop(s, "toon_mix", slider=True)
        layout.operator("paperzhu.skin_all", icon='MATERIAL')

class PAPERZHU_PT_shader_slot(Panel):
    bl_label = "单材质槽处理"
    bl_idname = "PAPERZHU_PT_shader_slot"
    bl_parent_id = "PAPERZHU_PT_shader"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Paper二分"

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        s = context.scene.paperzhu_settings
        layout.prop(s, "target_slot")
        layout.operator("paperzhu.skin_slot", icon='SHADING_TEXTURE')

CLASSES = (PAPERZHU_PT_shader, PAPERZHU_PT_shader_slot)

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
