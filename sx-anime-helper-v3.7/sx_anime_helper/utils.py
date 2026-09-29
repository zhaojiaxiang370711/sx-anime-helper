# Paper said：ciallo
import bpy
from .constants import COLOR_LOOK_MAP


def log(message: str):
    print(f"[SX Anime Helper] {message}")


def ensure_eevee(context):
    """尽量切换到 Eevee 渲染器，兼容不同 Blender 版本的枚举名。"""
    scene = context.scene
    enum_keys = set(bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys())
    for key in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if key in enum_keys:
            scene.render.engine = key
            return key
    return scene.render.engine


def get_selected_mesh_objects(context):
    return [obj for obj in context.selected_objects if obj.type == 'MESH']


def report_no_selection(operator):
    operator.report({'ERROR'}, "未选择模型")


def report_no_mesh(operator):
    operator.report({'ERROR'}, "请选择模型网格")


def safe_set_view_transform(scene, view_transform="Standard"):
    vs = scene.view_settings
    try:
        vs.view_transform = view_transform
    except Exception:
        log(f"当前版本无法设置 View Transform = {view_transform}，保留原值")


def safe_set_look(scene, preset_key: str):
    vs = scene.view_settings
    desired = COLOR_LOOK_MAP.get(preset_key, 'None')
    try:
        vs.look = desired
        return
    except Exception:
        pass

    try:
        enum_items = bpy.types.ColorManagedViewSettings.bl_rna.properties["look"].enum_items.keys()
        if desired in enum_items:
            vs.look = desired
        elif 'None' in enum_items:
            vs.look = 'None'
    except Exception:
        log("当前版本无法设置 Look，已跳过")


def find_material_output(node_tree):
    for node in node_tree.nodes:
        if node.type == 'OUTPUT_MATERIAL' and getattr(node, 'is_active_output', True):
            return node
    for node in node_tree.nodes:
        if node.type == 'OUTPUT_MATERIAL':
            return node
    return None


def find_principled_bsdf(node_tree):
    output = find_material_output(node_tree)
    if output and output.inputs.get("Surface") and output.inputs["Surface"].is_linked:
        from_node = output.inputs["Surface"].links[0].from_node
        if from_node.type == 'BSDF_PRINCIPLED':
            return from_node
    for node in node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            return node
    return None


def ensure_two_color_ramp(color_ramp, pos_a: float, pos_b: float):
    while len(color_ramp.elements) > 2:
        color_ramp.elements.remove(color_ramp.elements[-1])
    while len(color_ramp.elements) < 2:
        color_ramp.elements.new(0.5)
    color_ramp.elements[0].position = pos_a
    color_ramp.elements[1].position = pos_b
    return color_ramp.elements[0], color_ramp.elements[1]


def ensure_viewport_compositor_always(context):
    """把所有 3D 视图的视口合成器切到"总是/ALWAYS"。"""
    changed = 0

    space = getattr(context, 'space_data', None)
    shading = getattr(space, 'shading', None)
    if shading and hasattr(shading, 'use_compositor'):
        try:
            if shading.use_compositor != 'ALWAYS':
                shading.use_compositor = 'ALWAYS'
                changed += 1
        except Exception:
            pass

    wm = getattr(context, 'window_manager', None)
    if not wm:
        return changed
    for window in wm.windows:
        screen = window.screen
        if not screen:
            continue
        for area in screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                shading = getattr(space, 'shading', None)
                if not shading or not hasattr(shading, 'use_compositor'):
                    continue
                try:
                    if shading.use_compositor != 'ALWAYS':
                        shading.use_compositor = 'ALWAYS'
                        changed += 1
                except Exception:
                    continue
    return changed
