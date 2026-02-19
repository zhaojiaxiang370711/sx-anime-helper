# Paper said：ciallo
import os
import bpy
from .constants import OUTLINE_MATERIAL_NAME

def ensure_outline_material():
    mat = bpy.data.materials.get(OUTLINE_MATERIAL_NAME)
    if mat is None:
        mat = bpy.data.materials.new(name=OUTLINE_MATERIAL_NAME)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        out.location = (200, 0)
        em = nt.nodes.new("ShaderNodeEmission")
        em.location = (0, 0)
        em.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
        em.inputs["Strength"].default_value = 1.0
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    try:
        mat.use_backface_culling = True
    except Exception:
        pass
    return mat

def load_matcap_image(addon_dir):
    img = bpy.data.images.get("matcap01.png") or bpy.data.images.get("matcap01")
    if img:
        return img
    path = os.path.join(addon_dir, "matcap01.png")
    if os.path.exists(path):
        try:
            return bpy.data.images.load(path, check_existing=True)
        except Exception:
            return None
    return None
