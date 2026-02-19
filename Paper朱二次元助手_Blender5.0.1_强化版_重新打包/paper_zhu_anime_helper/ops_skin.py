# Paper said：ciallo
import os
import bpy
from bpy.types import Operator
from .utils_engine import ensure_eevee
from .constants import OUTLINE_MATERIAL_NAME, TAG
from .materials import load_matcap_image

def _find_output(nt):
    for n in nt.nodes:
        if n.type == 'OUTPUT_MATERIAL':
            return n
    return None

def _find_principled(nt):
    out = _find_output(nt)
    if out and out.inputs.get("Surface") and out.inputs["Surface"].is_linked:
        n = out.inputs["Surface"].links[0].from_node
        if n.type == 'BSDF_PRINCIPLED':
            return n
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n
    return None

def _clear_old(nt):
    for n in list(nt.nodes):
        if getattr(n, "label", "") == TAG or getattr(n, "name", "").startswith("PAPERZHU_"):
            nt.nodes.remove(n)

def _ensure(nt, node_type, name, loc):
    n = nt.nodes.get(name)
    if n and n.type == node_type:
        n.location = loc
        n.label = TAG
        return n
    n = nt.nodes.new(node_type)
    n.name = name
    n.label = TAG
    n.location = loc
    return n

def _ensure_colorramp_two(cr, p0, p1):
    while len(cr.elements) > 2:
        cr.elements.remove(cr.elements[-1])
    while len(cr.elements) < 2:
        cr.elements.new(0.5)
    cr.elements[0].position = p0
    cr.elements[1].position = p1
    return cr.elements[0], cr.elements[1]

def apply_highlight_skin(mat: bpy.types.Material, mix_factor: float) -> bool:
    if not mat or mat.name == OUTLINE_MATERIAL_NAME:
        return False
    if not mat.use_nodes or not mat.node_tree:
        return False

    nt = mat.node_tree
    links = nt.links
    bsdf = _find_principled(nt)
    if not bsdf:
        return False

    base_in = bsdf.inputs.get("Base Color")
    if not base_in:
        return False

    orig_link = base_in.links[0] if base_in.is_linked else None
    orig_default = tuple(base_in.default_value)
    orig_socket = None
    if orig_link:
        orig_socket = orig_link.from_socket
        links.remove(orig_link)

    _clear_old(nt)

    rgb = _ensure(nt, "ShaderNodeRGB", "PAPERZHU_OrigRGB", (-1100, 240))
    rgb.outputs[0].default_value = orig_default
    def orig_color():
        return orig_socket if orig_socket else rgb.outputs[0]

    diff = _ensure(nt, "ShaderNodeBsdfDiffuse", "PAPERZHU_Diffuse", (-860, 240))
    links.new(orig_color(), diff.inputs["Color"])

    s2r = _ensure(nt, "ShaderNodeShaderToRGB", "PAPERZHU_S2R_Diffuse", (-660, 240))
    links.new(diff.outputs["BSDF"], s2r.inputs["Shader"])

    ramp_mask = _ensure(nt, "ShaderNodeValToRGB", "PAPERZHU_Ramp_LightMask", (-460, 240))
    links.new(s2r.outputs["Color"], ramp_mask.inputs["Fac"])
    e0, e1 = _ensure_colorramp_two(ramp_mask.color_ramp, 0.43, 0.58)
    e0.color = (0,0,0,1)
    e1.color = (1,1,1,1)

    bc = _ensure(nt, "ShaderNodeBrightContrast", "PAPERZHU_ShadowBC", (-660, 40))
    bc.inputs["Bright"].default_value = -0.15
    bc.inputs["Contrast"].default_value = 0.15
    links.new(orig_color(), bc.inputs["Color"])

    mix_toon = _ensure(nt, "ShaderNodeMixRGB", "PAPERZHU_ToonMix", (-260, 200))
    mix_toon.blend_type = 'MIX'
    mix_toon.inputs["Fac"].default_value = 1.0
    links.new(ramp_mask.outputs["Color"], mix_toon.inputs["Fac"])
    links.new(bc.outputs["Color"], mix_toon.inputs["Color1"])
    links.new(orig_color(), mix_toon.inputs["Color2"])
    toon_color = mix_toon.outputs["Color"]

    glossy = _ensure(nt, "ShaderNodeBsdfGlossy", "PAPERZHU_Glossy", (-860, -160))
    glossy.inputs["Color"].default_value = (1,1,1,1)
    glossy.inputs["Roughness"].default_value = 0.15

    s2r_g = _ensure(nt, "ShaderNodeShaderToRGB", "PAPERZHU_S2R_Glossy", (-660, -160))
    links.new(glossy.outputs["BSDF"], s2r_g.inputs["Shader"])

    ramp_hi = _ensure(nt, "ShaderNodeValToRGB", "PAPERZHU_Ramp_HighlightMask", (-460, -160))
    links.new(s2r_g.outputs["Color"], ramp_hi.inputs["Fac"])
    h0, h1 = _ensure_colorramp_two(ramp_hi.color_ramp, 0.84, 0.93)
    h0.color = (0,0,0,1)
    h1.color = (1,1,1,1)

    hi_col = _ensure(nt, "ShaderNodeRGB", "PAPERZHU_HighlightColor", (-460, -340))
    hi_col.outputs[0].default_value = (1.0, 0.95, 0.92, 1.0)

    mul_hi = _ensure(nt, "ShaderNodeMixRGB", "PAPERZHU_HighlightMul", (-260, -160))
    mul_hi.blend_type = 'MULTIPLY'
    mul_hi.inputs["Fac"].default_value = 1.0
    links.new(ramp_hi.outputs["Color"], mul_hi.inputs["Color1"])
    links.new(hi_col.outputs[0], mul_hi.inputs["Color2"])

    add_hi = _ensure(nt, "ShaderNodeMixRGB", "PAPERZHU_AddHighlight", (-60, 120))
    add_hi.blend_type = 'ADD'
    add_hi.inputs["Fac"].default_value = 1.0
    links.new(toon_color, add_hi.inputs["Color1"])
    links.new(mul_hi.outputs["Color"], add_hi.inputs["Color2"])
    col_after_hi = add_hi.outputs["Color"]

    lw = _ensure(nt, "ShaderNodeLayerWeight", "PAPERZHU_LayerWeight", (-460, 520))
    lw.inputs["Blend"].default_value = 0.6

    ramp_edge = _ensure(nt, "ShaderNodeValToRGB", "PAPERZHU_Ramp_EdgeMask", (-260, 520))
    links.new(lw.outputs["Fresnel"], ramp_edge.inputs["Fac"])
    ed0, ed1 = _ensure_colorramp_two(ramp_edge.color_ramp, 0.55, 0.85)
    ed0.color = (0,0,0,1)
    ed1.color = (1,1,1,1)

    edge_col = _ensure(nt, "ShaderNodeRGB", "PAPERZHU_EdgeColor", (-260, 340))
    edge_col.outputs[0].default_value = (1,1,1,1)

    mul_edge = _ensure(nt, "ShaderNodeMixRGB", "PAPERZHU_EdgeMul", (-60, 420))
    mul_edge.blend_type = 'MULTIPLY'
    mul_edge.inputs["Fac"].default_value = 1.0
    links.new(ramp_edge.outputs["Color"], mul_edge.inputs["Color1"])
    links.new(edge_col.outputs[0], mul_edge.inputs["Color2"])

    add_edge = _ensure(nt, "ShaderNodeMixRGB", "PAPERZHU_AddEdge", (140, 200))
    add_edge.blend_type = 'ADD'
    add_edge.inputs["Fac"].default_value = 1.0
    links.new(col_after_hi, add_edge.inputs["Color1"])
    links.new(mul_edge.outputs["Color"], add_edge.inputs["Color2"])
    col_after_edge = add_edge.outputs["Color"]

    img = load_matcap_image(os.path.dirname(__file__))
    if img:
        texcoord = _ensure(nt, "ShaderNodeTexCoord", "PAPERZHU_TexCoord", (-660, -520))
        mapping = _ensure(nt, "ShaderNodeMapping", "PAPERZHU_Mapping", (-460, -520))
        mapping.inputs["Scale"].default_value = (1,1,1)
        links.new(texcoord.outputs["Normal"], mapping.inputs["Vector"])

        tex = _ensure(nt, "ShaderNodeTexImage", "PAPERZHU_MatcapTex", (-260, -520))
        tex.image = img
        tex.interpolation = 'Linear'
        tex.extension = 'CLIP'
        links.new(mapping.outputs["Vector"], tex.inputs["Vector"])

        strength = _ensure(nt, "ShaderNodeValue", "PAPERZHU_MatcapStrength", (-260, -700))
        strength.outputs[0].default_value = 0.15

        add_matcap = _ensure(nt, "ShaderNodeMixRGB", "PAPERZHU_AddMatcap", (340, 40))
        add_matcap.blend_type = 'ADD'
        links.new(strength.outputs[0], add_matcap.inputs["Fac"])
        links.new(col_after_edge, add_matcap.inputs["Color1"])
        links.new(tex.outputs["Color"], add_matcap.inputs["Color2"])
        stylized = add_matcap.outputs["Color"]
    else:
        stylized = col_after_edge

    mix_final = _ensure(nt, "ShaderNodeMixRGB", "PAPERZHU_FinalMix", (560, 180))
    mix_final.blend_type = 'MIX'
    mix_final.inputs["Fac"].default_value = float(mix_factor)
    links.new(orig_color(), mix_final.inputs["Color1"])
    links.new(stylized, mix_final.inputs["Color2"])
    links.new(mix_final.outputs["Color"], bsdf.inputs["Base Color"])

    return True

class PAPERZHU_OT_apply_skin_all(Operator):
    bl_idname = "paperzhu.skin_all"
    bl_label = "一键添加高光皮肤材质"
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):
        ensure_eevee(context)
        mix_val = context.scene.paperzhu_settings.toon_mix
        changed = 0
        for ob in context.selected_objects:
            if ob.type != 'MESH':
                continue
            for slot in ob.material_slots:
                if apply_highlight_skin(slot.material, mix_val):
                    changed += 1
        self.report({'INFO'}, f"已添加高光皮肤材质：{changed} 个材质（忽略 {OUTLINE_MATERIAL_NAME}）")
        return {'FINISHED'}

class PAPERZHU_OT_apply_skin_active(Operator):
    bl_idname = "paperzhu.skin_active"
    bl_label = "对当前材质添加高光皮肤材质"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.type == 'MESH' and obj.active_material is not None

    def execute(self, context):
        ensure_eevee(context)
        mix_val = context.scene.paperzhu_settings.toon_mix
        mat = context.object.active_material
        if mat and mat.name == OUTLINE_MATERIAL_NAME:
            self.report({'WARNING'}, f"当前材质是描边材质 {OUTLINE_MATERIAL_NAME}，已忽略")
            return {'CANCELLED'}
        if apply_highlight_skin(mat, mix_val):
            self.report({'INFO'}, f"已对当前材质添加高光皮肤材质：{mat.name}")
            return {'FINISHED'}
        self.report({'WARNING'}, "当前材质无法处理（未启用节点或缺少 Principled BSDF）")
        return {'CANCELLED'}

CLASSES = (PAPERZHU_OT_apply_skin_all, PAPERZHU_OT_apply_skin_active)

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
