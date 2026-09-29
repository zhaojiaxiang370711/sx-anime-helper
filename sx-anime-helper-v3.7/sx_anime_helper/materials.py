# Paper said：ciallo
import os
import bpy
from .constants import (
    OUTLINE_MATERIAL_NAME,
    OUTLINE_MODIFIER_NAME,
    OUTLINE_MATERIAL_FLAG,
    TAG,
    SKIN_REROUTE_NAME,
    SKIN_FINAL_MIX_NAME,
    SKIN_GLOSSY_NAME,
    SKIN_RAMP_LIGHT_NAME,
    SKIN_RAMP_HIGHLIGHT_NAME,
    SKIN_EDGE_RAMP_NAME,
    SKIN_MATCAP_ADD_NAME,
)
from .utils import find_principled_bsdf, ensure_two_color_ramp, log


# ---------- 描边 ----------

def _configure_outline_material_for_stable_fix(mat: bpy.types.Material):
    """效果优先的描边材质修复：尽量减少正面穿帮和异常阴影。"""
    if mat is None:
        return []

    changed = []

    def _try_set(owner, attr, value):
        if hasattr(owner, attr):
            try:
                old = getattr(owner, attr)
                if old != value:
                    setattr(owner, attr, value)
                    changed.append(f"{attr}={value}")
                return True
            except Exception:
                return False
        return False

    # 稳定方案：保持总背面剔除开启，并显式开启阴影与体积光探头剔除，
    # 这样可避免描边材质在 Blender 5.x 中出现整体发黑或脏阴影。
    _try_set(mat, 'use_backface_culling', True)
    _try_set(mat, 'use_backface_culling_shadow', True)
    _try_set(mat, 'use_backface_culling_lightprobe_volume', True)
    _try_set(mat, 'use_transparent_shadow', False)

    if getattr(mat, 'use_nodes', False) and mat.node_tree:
        nt = mat.node_tree
        out = None
        emission = None
        for node in nt.nodes:
            if node.type == 'OUTPUT_MATERIAL' and getattr(node, 'is_active_output', True):
                out = node
            elif node.bl_idname == 'ShaderNodeEmission':
                emission = node
        if out and emission and out.inputs.get('Surface'):
            try:
                for link in list(out.inputs['Surface'].links):
                    nt.links.remove(link)
                nt.links.new(emission.outputs['Emission'], out.inputs['Surface'])
                changed.append('surface=Emission')
            except Exception:
                pass
    return changed


def ensure_outline_material():
    mat = bpy.data.materials.get(OUTLINE_MATERIAL_NAME)
    if mat is None:
        mat = bpy.data.materials.new(name=OUTLINE_MATERIAL_NAME)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        out.location = (240, 0)
        emission = nt.nodes.new("ShaderNodeEmission")
        emission.location = (0, 0)
        emission.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
        emission.inputs["Strength"].default_value = 1.0
        nt.links.new(emission.outputs["Emission"], out.inputs["Surface"])
    mat[OUTLINE_MATERIAL_FLAG] = True
    _configure_outline_material_for_stable_fix(mat)
    return mat


def apply_outline_to_object(obj: bpy.types.Object, thickness: float) -> str:
    if obj.type != 'MESH':
        return 'SKIPPED'

    outline_mat = ensure_outline_material()
    names = [m.name for m in obj.data.materials if m]
    if OUTLINE_MATERIAL_NAME not in names:
        obj.data.materials.append(outline_mat)

    modifier = obj.modifiers.get(OUTLINE_MODIFIER_NAME)
    if modifier is None:
        modifier = obj.modifiers.new(OUTLINE_MODIFIER_NAME, 'SOLIDIFY')

    modifier.thickness = thickness
    modifier.offset = 0.0
    modifier.material_offset = max(0, len(obj.material_slots) - 1)
    modifier.use_even_offset = False
    if hasattr(modifier, "use_rim"):
        modifier.use_rim = False
    if hasattr(modifier, "use_rim_only"):
        modifier.use_rim_only = False
    if hasattr(modifier, "use_flip_normals"):
        modifier.use_flip_normals = True
    if hasattr(modifier, "use_quality_normals"):
        modifier.use_quality_normals = True
    return 'OK'


def apply_outline_fix_to_object(obj: bpy.types.Object, thickness: float) -> str:
    result = apply_outline_to_object(obj, thickness)
    if obj.type != 'MESH':
        return result

    outline_mat = bpy.data.materials.get(OUTLINE_MATERIAL_NAME)
    changed_attrs = _configure_outline_material_for_stable_fix(outline_mat)
    if changed_attrs:
        log(f"描边材质 {outline_mat.name} 已应用稳定修复设置: {changed_attrs}")
    return 'OK'


def remove_outline_from_object(obj: bpy.types.Object) -> bool:
    if obj.type != 'MESH':
        return False

    removed = False
    modifier = obj.modifiers.get(OUTLINE_MODIFIER_NAME)
    if modifier:
        obj.modifiers.remove(modifier)
        removed = True

    for idx in range(len(obj.data.materials) - 1, -1, -1):
        mat = obj.data.materials[idx]
        if mat and mat.name == OUTLINE_MATERIAL_NAME:
            obj.data.materials.pop(index=idx)
            removed = True

    return removed


def update_outline_on_objects(objects, thickness: float):
    for obj in objects:
        mod = obj.modifiers.get(OUTLINE_MODIFIER_NAME)
        if mod:
            mod.thickness = thickness
            mod.material_offset = max(0, len(obj.material_slots) - 1)


def cleanup_unused_outline_material():
    mat = bpy.data.materials.get(OUTLINE_MATERIAL_NAME)
    if mat and mat.users == 0:
        bpy.data.materials.remove(mat)
        log("已清理未使用的描边材质")


# ---------- 高光皮肤 ----------

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


def _remove_tagged_nodes(node_tree, remove_reroute: bool = False):
    for node in list(node_tree.nodes):
        if node.name == SKIN_REROUTE_NAME and not remove_reroute:
            continue
        if node.get("sx_skin_node"):
            node_tree.nodes.remove(node)


def _ensure_node(node_tree, node_type: str, name: str, location):
    node = node_tree.nodes.get(name)
    if node is None or node.bl_idname != node_type:
        if node is not None:
            node_tree.nodes.remove(node)
        node = node_tree.nodes.new(node_type)
        node.name = name
    node.location = location
    node.label = TAG
    node["sx_skin_node"] = True
    return node


def _prepare_original_color_source(node_tree, bsdf):
    base_input = bsdf.inputs.get("Base Color")
    if base_input is None:
        return None

    reroute = node_tree.nodes.get(SKIN_REROUTE_NAME)
    if reroute is None or reroute.bl_idname != 'NodeReroute':
        if reroute is not None:
            node_tree.nodes.remove(reroute)
        reroute = node_tree.nodes.new('NodeReroute')
        reroute.name = SKIN_REROUTE_NAME
        reroute.location = (-1040, 240)
        reroute.label = TAG
        reroute["sx_skin_node"] = True

    # 已经存在原始颜色缓存时，保留它，只断开当前 Base Color 链接即可。
    if reroute.inputs[0].is_linked:
        for link in list(base_input.links):
            node_tree.links.remove(link)
        return reroute

    if base_input.is_linked:
        source_socket = base_input.links[0].from_socket
        node_tree.links.remove(base_input.links[0])
        node_tree.links.new(source_socket, reroute.inputs[0])
    else:
        rgb = _ensure_node(node_tree, 'ShaderNodeRGB', 'SX_OrigRGB', (-1280, 240))
        rgb.outputs[0].default_value = tuple(base_input.default_value)
        node_tree.links.new(rgb.outputs[0], reroute.inputs[0])
    return reroute


def apply_highlight_skin(mat: bpy.types.Material, mix_factor: float, glossy_roughness: float) -> bool:
    if not mat:
        return False
    if mat.name == OUTLINE_MATERIAL_NAME:
        return False
    if not mat.use_nodes or not mat.node_tree:
        return False

    node_tree = mat.node_tree
    links = node_tree.links
    bsdf = find_principled_bsdf(node_tree)
    if bsdf is None:
        return False

    reroute = _prepare_original_color_source(node_tree, bsdf)
    if reroute is None:
        return False

    _remove_tagged_nodes(node_tree, remove_reroute=False)
    reroute = _prepare_original_color_source(node_tree, bsdf)

    diffuse = _ensure_node(node_tree, 'ShaderNodeBsdfDiffuse', 'SX_Diffuse', (-820, 240))
    shader_to_rgb = _ensure_node(node_tree, 'ShaderNodeShaderToRGB', 'SX_S2R_Diffuse', (-620, 240))
    ramp_light = _ensure_node(node_tree, 'ShaderNodeValToRGB', SKIN_RAMP_LIGHT_NAME, (-420, 240))
    shadow_bc = _ensure_node(node_tree, 'ShaderNodeBrightContrast', 'SX_ShadowBC', (-620, 30))
    mix_toon = _ensure_node(node_tree, 'ShaderNodeMixRGB', 'SX_ToonMix', (-180, 180))

    glossy = _ensure_node(node_tree, 'ShaderNodeBsdfGlossy', SKIN_GLOSSY_NAME, (-820, -160))
    glossy.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    glossy.inputs['Roughness'].default_value = glossy_roughness

    s2r_glossy = _ensure_node(node_tree, 'ShaderNodeShaderToRGB', 'SX_S2R_Glossy', (-620, -160))
    ramp_highlight = _ensure_node(node_tree, 'ShaderNodeValToRGB', SKIN_RAMP_HIGHLIGHT_NAME, (-420, -160))
    highlight_color = _ensure_node(node_tree, 'ShaderNodeRGB', 'SX_HighlightColor', (-420, -330))
    highlight_mul = _ensure_node(node_tree, 'ShaderNodeMixRGB', 'SX_HighlightMul', (-180, -160))
    add_highlight = _ensure_node(node_tree, 'ShaderNodeMixRGB', 'SX_AddHighlight', (20, 90))

    layer_weight = _ensure_node(node_tree, 'ShaderNodeLayerWeight', 'SX_LayerWeight', (-420, 500))
    edge_ramp = _ensure_node(node_tree, 'ShaderNodeValToRGB', SKIN_EDGE_RAMP_NAME, (-220, 500))
    edge_color = _ensure_node(node_tree, 'ShaderNodeRGB', 'SX_EdgeColor', (-220, 330))
    edge_mul = _ensure_node(node_tree, 'ShaderNodeMixRGB', 'SX_EdgeMul', (-20, 390))
    add_edge = _ensure_node(node_tree, 'ShaderNodeMixRGB', 'SX_AddEdge', (200, 160))
    final_mix = _ensure_node(node_tree, 'ShaderNodeMixRGB', SKIN_FINAL_MIX_NAME, (560, 180))

    shadow_bc.inputs['Bright'].default_value = -0.15
    shadow_bc.inputs['Contrast'].default_value = 0.15

    mix_toon.blend_type = 'MIX'
    mix_toon.inputs['Fac'].default_value = 1.0

    h0, h1 = ensure_two_color_ramp(ramp_highlight.color_ramp, 0.84, 0.93)
    h0.color = (0.0, 0.0, 0.0, 1.0)
    h1.color = (1.0, 1.0, 1.0, 1.0)
    l0, l1 = ensure_two_color_ramp(ramp_light.color_ramp, 0.43, 0.58)
    l0.color = (0.0, 0.0, 0.0, 1.0)
    l1.color = (1.0, 1.0, 1.0, 1.0)
    e0, e1 = ensure_two_color_ramp(edge_ramp.color_ramp, 0.55, 0.85)
    e0.color = (0.0, 0.0, 0.0, 1.0)
    e1.color = (1.0, 1.0, 1.0, 1.0)

    highlight_color.outputs[0].default_value = (1.0, 0.95, 0.92, 1.0)
    edge_color.outputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    layer_weight.inputs['Blend'].default_value = 0.6

    highlight_mul.blend_type = 'MULTIPLY'
    highlight_mul.inputs['Fac'].default_value = 1.0
    add_highlight.blend_type = 'ADD'
    add_highlight.inputs['Fac'].default_value = 1.0
    edge_mul.blend_type = 'MULTIPLY'
    edge_mul.inputs['Fac'].default_value = 1.0
    add_edge.blend_type = 'ADD'
    add_edge.inputs['Fac'].default_value = 1.0
    final_mix.blend_type = 'MIX'
    final_mix.inputs['Fac'].default_value = mix_factor

    # Matcap 质感叠加
    img = load_matcap_image(os.path.dirname(__file__))
    if img:
        texcoord = _ensure_node(node_tree, 'ShaderNodeTexCoord', 'SX_TexCoord', (-620, -520))
        mapping = _ensure_node(node_tree, 'ShaderNodeMapping', 'SX_Mapping', (-420, -520))
        mapping.inputs['Scale'].default_value = (1.0, 1.0, 1.0)
        matcap_tex = _ensure_node(node_tree, 'ShaderNodeTexImage', 'SX_MatcapTex', (-220, -520))
        matcap_tex.image = img
        matcap_tex.interpolation = 'Linear'
        matcap_tex.extension = 'CLIP'
        matcap_strength = _ensure_node(node_tree, 'ShaderNodeValue', 'SX_MatcapStrength', (-220, -700))
        matcap_strength.outputs[0].default_value = 0.15
        add_matcap = _ensure_node(node_tree, 'ShaderNodeMixRGB', SKIN_MATCAP_ADD_NAME, (380, 60))
        add_matcap.blend_type = 'ADD'
    else:
        texcoord = mapping = matcap_tex = matcap_strength = add_matcap = None

    # 先清理旧链接，避免重复连线
    relink_nodes = [diffuse, shader_to_rgb, ramp_light, shadow_bc, mix_toon, glossy, s2r_glossy,
                    ramp_highlight, highlight_mul, add_highlight, layer_weight, edge_ramp,
                    edge_mul, add_edge, final_mix]
    if add_matcap is not None:
        relink_nodes += [mapping, matcap_tex, add_matcap]
    for node in relink_nodes:
        for input_socket in getattr(node, 'inputs', []):
            for link in list(input_socket.links):
                links.remove(link)

    links.new(reroute.outputs[0], diffuse.inputs['Color'])
    links.new(diffuse.outputs['BSDF'], shader_to_rgb.inputs['Shader'])
    links.new(shader_to_rgb.outputs['Color'], ramp_light.inputs['Fac'])
    links.new(reroute.outputs[0], shadow_bc.inputs['Color'])
    links.new(ramp_light.outputs['Color'], mix_toon.inputs['Fac'])
    links.new(shadow_bc.outputs['Color'], mix_toon.inputs['Color1'])
    links.new(reroute.outputs[0], mix_toon.inputs['Color2'])

    links.new(glossy.outputs['BSDF'], s2r_glossy.inputs['Shader'])
    links.new(s2r_glossy.outputs['Color'], ramp_highlight.inputs['Fac'])
    links.new(ramp_highlight.outputs['Color'], highlight_mul.inputs['Color1'])
    links.new(highlight_color.outputs[0], highlight_mul.inputs['Color2'])
    links.new(mix_toon.outputs['Color'], add_highlight.inputs['Color1'])
    links.new(highlight_mul.outputs['Color'], add_highlight.inputs['Color2'])

    links.new(layer_weight.outputs['Fresnel'], edge_ramp.inputs['Fac'])
    links.new(edge_ramp.outputs['Color'], edge_mul.inputs['Color1'])
    links.new(edge_color.outputs[0], edge_mul.inputs['Color2'])
    links.new(add_highlight.outputs['Color'], add_edge.inputs['Color1'])
    links.new(edge_mul.outputs['Color'], add_edge.inputs['Color2'])

    if add_matcap is not None:
        links.new(texcoord.outputs['Normal'], mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], matcap_tex.inputs['Vector'])
        links.new(matcap_strength.outputs[0], add_matcap.inputs['Fac'])
        links.new(add_edge.outputs['Color'], add_matcap.inputs['Color1'])
        links.new(matcap_tex.outputs['Color'], add_matcap.inputs['Color2'])
        stylized_color = add_matcap.outputs['Color']
    else:
        stylized_color = add_edge.outputs['Color']

    links.new(reroute.outputs[0], final_mix.inputs['Color1'])
    links.new(stylized_color, final_mix.inputs['Color2'])
    links.new(final_mix.outputs['Color'], bsdf.inputs['Base Color'])

    mat['sx_skin_enabled'] = True
    return True


def remove_highlight_skin(mat: bpy.types.Material) -> bool:
    if not mat or not mat.use_nodes or not mat.node_tree:
        return False

    node_tree = mat.node_tree
    bsdf = find_principled_bsdf(node_tree)
    reroute = node_tree.nodes.get(SKIN_REROUTE_NAME)
    if bsdf is None or reroute is None:
        return False

    base_input = bsdf.inputs.get('Base Color')
    if base_input is None:
        return False

    for link in list(base_input.links):
        node_tree.links.remove(link)

    source_links = list(reroute.inputs[0].links)
    if source_links:
        source_socket = source_links[0].from_socket
        node_tree.links.new(source_socket, base_input)

    _remove_tagged_nodes(node_tree, remove_reroute=True)
    if 'sx_skin_enabled' in mat:
        del mat['sx_skin_enabled']
    return True


def update_skin_on_material(mat: bpy.types.Material, mix_factor: float, glossy_roughness: float):
    if not mat or not mat.use_nodes or not mat.node_tree:
        return
    nt = mat.node_tree
    final_mix = nt.nodes.get(SKIN_FINAL_MIX_NAME)
    glossy = nt.nodes.get(SKIN_GLOSSY_NAME)
    if final_mix:
        final_mix.inputs['Fac'].default_value = mix_factor
    if glossy:
        glossy.inputs['Roughness'].default_value = glossy_roughness


def iter_unique_materials_from_objects(objects):
    seen = set()
    for obj in objects:
        if obj.type != 'MESH':
            continue
        for slot in obj.material_slots:
            mat = slot.material
            if mat and mat.name not in seen:
                seen.add(mat.name)
                yield mat


def update_skin_on_objects(objects, mix_factor: float, glossy_roughness: float):
    for mat in iter_unique_materials_from_objects(objects):
        update_skin_on_material(mat, mix_factor, glossy_roughness)
