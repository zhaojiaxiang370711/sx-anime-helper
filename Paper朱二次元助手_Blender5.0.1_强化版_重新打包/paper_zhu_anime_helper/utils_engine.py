# Paper said：ciallo
import bpy

def ensure_eevee(context):
    enum = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys()
    if "BLENDER_EEVEE" in enum:
        context.scene.render.engine = "BLENDER_EEVEE"
