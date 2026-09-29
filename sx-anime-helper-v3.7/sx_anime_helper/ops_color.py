# Paper said：ciallo
import bpy
from bpy.types import Operator
from .utils import ensure_eevee, safe_set_look, safe_set_view_transform
from .props import _apply_color


class SX_OT_color(Operator):
    bl_idname = "sx_anime.color"
    bl_label = "一键二次元色彩"
    bl_description = "一键设置适合二次元渲染的色彩管理"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.sx_anime_settings
        if settings.auto_switch_eevee:
            ensure_eevee(context)
        _apply_color(context.scene, settings)
        self.report({'INFO'}, "已应用风格化色彩管理")
        return {'FINISHED'}


class SX_OT_color_remove(Operator):
    bl_idname = "sx_anime.color_remove"
    bl_label = "撤销色彩"
    bl_description = "恢复较中性的色彩管理设置"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        safe_set_view_transform(context.scene, "Standard")
        safe_set_look(context.scene, 'NONE')
        context.scene.view_settings.exposure = 0.0
        self.report({'INFO'}, "已恢复默认色彩管理")
        return {'FINISHED'}


CLASSES = (SX_OT_color, SX_OT_color_remove)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
