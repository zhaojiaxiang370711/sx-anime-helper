# Paper said：ciallo
import bpy
from bpy.props import FloatProperty, EnumProperty, PointerProperty, BoolProperty
from .constants import OUTLINE_MATERIAL_NAME, COLOR_LOOK_PRESETS
from .utils import get_selected_mesh_objects, safe_set_look, safe_set_view_transform
from .materials import update_outline_on_objects, update_skin_on_objects
from .compositor import update_glow_setup


def enum_material_slots(self, context):
    obj = context.object
    if obj is None or obj.type != 'MESH':
        return []
    items = []
    for idx, slot in enumerate(obj.material_slots):
        mat = slot.material
        if mat and mat.name == OUTLINE_MATERIAL_NAME:
            continue
        name = mat.name if mat else f"材质槽 {idx+1}"
        items.append((str(idx), f"[{idx}] {name}", ""))
    return items


def _update_outline(self, context):
    objects = get_selected_mesh_objects(context)
    if objects:
        update_outline_on_objects(objects, context.scene.sx_anime_settings.outline_thickness)


def _update_skin(self, context):
    settings = context.scene.sx_anime_settings
    objects = get_selected_mesh_objects(context)
    if objects:
        update_skin_on_objects(objects, settings.toon_mix, settings.skin_roughness)


def _apply_color(scene, settings):
    if settings.color_look == 'AGX_HIGH':
        safe_set_view_transform(scene, "AgX")
        safe_set_look(scene, 'AGX_HIGH')
    else:
        safe_set_view_transform(scene, "Standard")
        safe_set_look(scene, settings.color_look)
    scene.view_settings.exposure = settings.color_exposure


def _update_color(self, context):
    scene = context.scene
    settings = scene.sx_anime_settings
    _apply_color(scene, settings)


def _update_glow(self, context):
    scene = context.scene
    if scene.get('sx_glow_setup'):
        update_glow_setup(scene, scene.sx_anime_settings.glow_threshold)


class SX_PG_settings(bpy.types.PropertyGroup):
    outline_thickness: FloatProperty(
        name="描边粗细",
        default=0.001,
        min=0.0,
        max=0.05,
        precision=4,
        update=_update_outline,
    )
    color_look: EnumProperty(
        name="色彩对比",
        items=COLOR_LOOK_PRESETS,
        default='MEDIUM_HIGH',
        update=_update_color,
    )
    color_exposure: FloatProperty(
        name="色彩曝光",
        default=0.0,
        min=-2.0,
        max=2.0,
        update=_update_color,
    )
    toon_mix: FloatProperty(
        name="二分混合程度",
        min=0.0, max=1.0,
        default=0.6,
        subtype='FACTOR',
        update=_update_skin,
    )
    skin_roughness: FloatProperty(
        name="高光粗糙度",
        default=0.15,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
        update=_update_skin,
    )
    glow_threshold: FloatProperty(
        name="辉光阈值",
        default=0.85,
        min=0.0,
        max=10.0,
        update=_update_glow,
    )
    target_slot: EnumProperty(
        name="目标材质槽",
        description="选择要处理的材质槽（会自动忽略描边材质）",
        items=enum_material_slots,
    )
    auto_switch_eevee: BoolProperty(
        name="执行时自动切到 Eevee",
        default=True,
    )


CLASSES = (SX_PG_settings,)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.sx_anime_settings = PointerProperty(type=SX_PG_settings)


def unregister():
    if hasattr(bpy.types.Scene, 'sx_anime_settings'):
        del bpy.types.Scene.sx_anime_settings
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
