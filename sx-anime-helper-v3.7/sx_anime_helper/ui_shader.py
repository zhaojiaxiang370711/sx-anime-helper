# Paper said：ciallo
import bpy
from bpy.types import Panel
from .constants import ADDON_CATEGORY


class SX_PT_shader(Panel):
    bl_label = "SX Anime Helper"
    bl_idname = "SX_PT_shader"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY

    @classmethod
    def poll(cls, context):
        return context.space_data and getattr(context.space_data, "tree_type", "") == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout
        s = context.scene.sx_anime_settings
        layout.prop(s, "toon_mix", slider=True)
        layout.prop(s, "skin_roughness", slider=True)
        row = layout.row(align=True)
        row.operator("sx_anime.skin_all", icon='MATERIAL')
        row.operator("sx_anime.skin_remove", text="撤销", icon='LOOP_BACK')


class SX_PT_shader_slot(Panel):
    bl_label = "单材质槽处理"
    bl_idname = "SX_PT_shader_slot"
    bl_parent_id = "SX_PT_shader"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        s = context.scene.sx_anime_settings
        layout.prop(s, "target_slot")
        layout.operator("sx_anime.skin_slot", icon='SHADING_TEXTURE')


CLASSES = (SX_PT_shader, SX_PT_shader_slot)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
