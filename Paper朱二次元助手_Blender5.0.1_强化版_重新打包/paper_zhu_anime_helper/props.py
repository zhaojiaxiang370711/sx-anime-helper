# Paper said：ciallo
import bpy
from bpy.props import FloatProperty, EnumProperty, PointerProperty
from .constants import OUTLINE_MATERIAL_NAME

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

class PAPERZHU_PG_settings(bpy.types.PropertyGroup):
    toon_mix: FloatProperty(
        name="二分混合程度",
        min=0.0, max=1.0,
        default=0.6,
        subtype='FACTOR'
    )
    target_slot: EnumProperty(
        name="目标材质槽",
        description="选择要处理的材质槽（会自动忽略描边材质）",
        items=enum_material_slots
    )

CLASSES = (PAPERZHU_PG_settings,)

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.paperzhu_settings = PointerProperty(type=PAPERZHU_PG_settings)

def unregister():
    del bpy.types.Scene.paperzhu_settings
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
