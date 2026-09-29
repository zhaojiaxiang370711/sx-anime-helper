# Paper said：ciallo
import bpy
from bpy.types import Operator
from .utils import ensure_eevee, ensure_viewport_compositor_always
from .compositor import ensure_glow_setup, remove_glow_setup


class SX_OT_apply_glow(Operator):
    bl_idname = "sx_anime.glow"
    bl_label = "一键SX_Anime_Glow"
    bl_description = "在合成器中一键创建辉光节点，并只保留阈值调节"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.sx_anime_settings
        if settings.auto_switch_eevee:
            ensure_eevee(context)

        ensure_glow_setup(context.scene, settings.glow_threshold)
        changed_views = ensure_viewport_compositor_always(context)
        self.report({'INFO'}, f"已创建一键辉光，并将 {changed_views} 个 3D 视图的合成器切到总是")
        return {'FINISHED'}


class SX_OT_remove_glow(Operator):
    bl_idname = "sx_anime.glow_remove"
    bl_label = "撤销辉光"
    bl_description = "移除插件创建的辉光节点并恢复直连输出"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if remove_glow_setup(context.scene):
            self.report({'INFO'}, "已移除合成器辉光")
            return {'FINISHED'}
        self.report({'WARNING'}, "未找到可移除的插件辉光节点")
        return {'CANCELLED'}


CLASSES = (SX_OT_apply_glow, SX_OT_remove_glow)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
