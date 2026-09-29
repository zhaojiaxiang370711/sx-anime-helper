# Paper said：ciallo
import bpy
from bpy.types import Panel
from .constants import ADDON_CATEGORY


class SX_PT_view3d(Panel):
    bl_label = "SX Anime Helper"
    bl_idname = "SX_PT_view3d"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = ADDON_CATEGORY

    def draw(self, context):
        layout = self.layout
        s = context.scene.sx_anime_settings

        box = layout.box()
        row = box.row(align=True)
        row.label(text="一键添加描边", icon='MOD_SOLIDIFY')
        row.operator("sx_anime.outline", text="应用")
        row.operator("sx_anime.outline_fix", text="修复")
        row.operator("sx_anime.outline_remove", text="撤销", icon='LOOP_BACK')
        box.prop(s, "outline_thickness", slider=True)

        box = layout.box()
        row = box.row(align=True)
        row.label(text="一键二次元色彩", icon='COLOR')
        row.operator("sx_anime.color", text="应用")
        row.operator("sx_anime.color_remove", text="撤销", icon='LOOP_BACK')
        box.prop(s, "color_look")
        box.prop(s, "color_exposure", slider=True)

        box = layout.box()
        row = box.row(align=True)
        row.label(text="一键添加高光皮肤", icon='MATERIAL')
        row.operator("sx_anime.skin_all", text="应用")
        row.operator("sx_anime.skin_remove", text="撤销", icon='LOOP_BACK')
        box.prop(s, "toon_mix", slider=True)
        box.prop(s, "skin_roughness", slider=True)

        box = layout.box()
        row = box.row(align=True)
        row.label(text="一键SX_Anime_Glow", icon='NODE_COMPOSITING')
        row.operator("sx_anime.glow", text="应用")
        row.operator("sx_anime.glow_remove", text="撤销", icon='LOOP_BACK')
        box.prop(s, "glow_threshold", slider=True)

        box = layout.box()
        box.label(text="单材质槽处理", icon='SHADING_TEXTURE')
        box.prop(s, "target_slot")
        box.operator("sx_anime.skin_slot")

        layout.separator()
        layout.prop(s, "auto_switch_eevee")
        layout.label(text="提示：参数会实时更新已应用效果", icon='INFO')


CLASSES = (SX_PT_view3d,)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
