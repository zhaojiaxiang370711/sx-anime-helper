# Paper said：ciallo
import bpy
from bpy.types import Operator
from .utils import ensure_eevee, get_selected_mesh_objects, report_no_selection, report_no_mesh
from .materials import (
    apply_outline_to_object,
    apply_outline_fix_to_object,
    remove_outline_from_object,
    cleanup_unused_outline_material,
)


def _ensure_mesh_selection(operator, context):
    if not context.selected_objects:
        report_no_selection(operator)
        return None
    objects = get_selected_mesh_objects(context)
    if not objects:
        report_no_mesh(operator)
        return None
    return objects


class SX_OT_outline(Operator):
    bl_idname = "sx_anime.outline"
    bl_label = "一键添加黑色描边"
    bl_description = "给选中的网格对象一键添加实体化描边"
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
            if apply_outline_to_object(obj, settings.outline_thickness) == 'OK':
                changed += 1
        self.report({'INFO'}, f"已为 {changed} 个对象添加/更新描边")
        return {'FINISHED'}


class SX_OT_outline_fix(Operator):
    bl_idname = "sx_anime.outline_fix"
    bl_label = "修复描边"
    bl_description = "可选修复：按效果优先的方式减少脸部、头发与眼周的描边脏阴影和正面穿帮"
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
            if apply_outline_fix_to_object(obj, settings.outline_thickness) == 'OK':
                changed += 1
        self.report({'INFO'}, f"已为 {changed} 个对象应用可选描边修复")
        return {'FINISHED'}


class SX_OT_outline_remove(Operator):
    bl_idname = "sx_anime.outline_remove"
    bl_label = "撤销描边"
    bl_description = "移除选中对象上的描边材质和实体化描边"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = _ensure_mesh_selection(self, context)
        if objects is None:
            return {'CANCELLED'}

        removed = 0
        for obj in objects:
            if remove_outline_from_object(obj):
                removed += 1
        cleanup_unused_outline_material()
        self.report({'INFO'}, f"已从 {removed} 个对象移除描边")
        return {'FINISHED'}


CLASSES = (SX_OT_outline, SX_OT_outline_fix, SX_OT_outline_remove)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
