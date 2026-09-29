# Paper said：ciallo
import bpy
from bpy.types import Operator
from .utils import ensure_eevee, get_selected_mesh_objects, report_no_selection, report_no_mesh
from .constants import OUTLINE_MATERIAL_NAME
from .materials import apply_highlight_skin, remove_highlight_skin


def _ensure_mesh_selection(operator, context):
    if not context.selected_objects:
        report_no_selection(operator)
        return None
    objects = get_selected_mesh_objects(context)
    if not objects:
        report_no_mesh(operator)
        return None
    return objects


class SX_OT_apply_skin_all(Operator):
    bl_idname = "sx_anime.skin_all"
    bl_label = "一键添加高光皮肤材质"
    bl_description = "为选中对象的全部材质一键添加二次元高光皮肤节点"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = _ensure_mesh_selection(self, context)
        if objects is None:
            return {'CANCELLED'}

        settings = context.scene.sx_anime_settings
        if settings.auto_switch_eevee:
            ensure_eevee(context)

        changed = 0
        for obj in objects:
            for slot in obj.material_slots:
                if apply_highlight_skin(slot.material, settings.toon_mix, settings.skin_roughness):
                    changed += 1

        if changed == 0:
            self.report({'WARNING'}, "没有可处理的材质：请确认材质启用了节点并包含 Principled BSDF")
            return {'CANCELLED'}
        self.report({'INFO'}, f"已添加高光皮肤材质：{changed} 个材质（忽略 {OUTLINE_MATERIAL_NAME}）")
        return {'FINISHED'}


class SX_OT_apply_skin_active(Operator):
    bl_idname = "sx_anime.skin_active"
    bl_label = "对当前材质添加高光皮肤材质"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.type == 'MESH' and obj.active_material is not None

    def execute(self, context):
        settings = context.scene.sx_anime_settings
        if settings.auto_switch_eevee:
            ensure_eevee(context)
        mat = context.object.active_material
        if mat and mat.name == OUTLINE_MATERIAL_NAME:
            self.report({'WARNING'}, f"当前材质是描边材质 {OUTLINE_MATERIAL_NAME}，已忽略")
            return {'CANCELLED'}
        if apply_highlight_skin(mat, settings.toon_mix, settings.skin_roughness):
            self.report({'INFO'}, f"已对当前材质添加高光皮肤材质：{mat.name}")
            return {'FINISHED'}
        self.report({'WARNING'}, "当前材质无法处理（未启用节点或缺少 Principled BSDF）")
        return {'CANCELLED'}


class SX_OT_remove_skin(Operator):
    bl_idname = "sx_anime.skin_remove"
    bl_label = "撤销高光皮肤"
    bl_description = "移除选中对象上由插件创建的高光皮肤节点，并恢复原始底色连线"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = _ensure_mesh_selection(self, context)
        if objects is None:
            return {'CANCELLED'}

        removed = 0
        seen = set()
        for obj in objects:
            for slot in obj.material_slots:
                mat = slot.material
                if mat and mat.name not in seen:
                    seen.add(mat.name)
                    if remove_highlight_skin(mat):
                        removed += 1

        if removed == 0:
            self.report({'WARNING'}, "未找到可撤销的高光皮肤节点")
            return {'CANCELLED'}
        self.report({'INFO'}, f"已恢复 {removed} 个材质")
        return {'FINISHED'}


CLASSES = (SX_OT_apply_skin_all, SX_OT_apply_skin_active, SX_OT_remove_skin)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
