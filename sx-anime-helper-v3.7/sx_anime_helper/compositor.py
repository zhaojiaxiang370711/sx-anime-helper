# Paper said：ciallo
import bpy
from .constants import (
    COMPOSITOR_TREE_FLAG,
    COMPOSITOR_GLOW_GROUP_NAME,
    COMPOSITOR_GLOW_GROUP_NODE_NAME,
    COMPOSITOR_VIEWER_NAME,
    COMPOSITOR_COMPOSITE_NAME,
    COMPOSITOR_RLAYERS_NAME,
)


GLOW_NODE_NAMES = {
    "bloom_blur_small": "PAPER_GLOW_BLUR_SMALL",
    "bloom_blur_mid": "PAPER_GLOW_BLUR_MID",
    "bloom_blur_large": "PAPER_GLOW_BLUR_LARGE",
    "bloom_mix_small": "PAPER_GLOW_MIX_SMALL",
    "bloom_mix_mid": "PAPER_GLOW_MIX_MID",
    "bloom_mix_large": "PAPER_GLOW_MIX_LARGE",
    "bloom_add_a": "PAPER_GLOW_ADD_A",
    "bloom_add_b": "PAPER_GLOW_ADD_B",
    "bloom_screen": "PAPER_GLOW_SCREEN",
    "tonemap_mix_a": "PAPER_TONEMAP_MIX_A",
    "tonemap_mix_b": "PAPER_TONEMAP_MIX_B",
    "tonemap_mix_out": "PAPER_TONEMAP_MIX_OUT",
}


def _new_supported(nodes, *candidates):
    last_error = None
    for node_type in candidates:
        try:
            return nodes.new(node_type)
        except Exception as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise RuntimeError("No supported node type candidates")


def _find_or_create(tree, node_type: str, name: str, location):
    node = tree.nodes.get(name)
    if node is None or node.bl_idname != node_type:
        if node is not None:
            tree.nodes.remove(node)
        node = tree.nodes.new(node_type)
        node.name = name
    node.location = location
    node["sx_compositor_node"] = True
    return node


def _is_blender_5_compositor(scene) -> bool:
    return hasattr(scene, "compositing_node_group")


def _ensure_output_socket_for_blender5(tree):
    if not hasattr(tree, "interface"):
        return
    for item in tree.interface.items_tree:
        if getattr(item, 'item_type', None) == 'SOCKET' and getattr(item, 'in_out', None) == 'OUTPUT':
            return
    tree.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')


def _clear_interface(tree):
    if hasattr(tree, "interface"):
        items = list(tree.interface.items_tree)
        for item in items:
            if getattr(item, "item_type", None) == 'SOCKET':
                try:
                    tree.interface.remove(item)
                except Exception:
                    pass
        return

    while len(tree.inputs):
        tree.inputs.remove(tree.inputs[0])
    while len(tree.outputs):
        tree.outputs.remove(tree.outputs[0])


def _add_interface_socket(tree, name: str, in_out: str, socket_type: str):
    if hasattr(tree, "interface"):
        return tree.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
    if in_out == 'INPUT':
        return tree.inputs.new(socket_type, name)
    return tree.outputs.new(socket_type, name)


def get_or_create_compositor_tree(scene):
    if _is_blender_5_compositor(scene):
        tree = scene.compositing_node_group
        if tree is None:
            tree = bpy.data.node_groups.new(name=f"{scene.name}_SXComp", type='CompositorNodeTree')
            scene.compositing_node_group = tree
            _ensure_output_socket_for_blender5(tree)
        else:
            _ensure_output_socket_for_blender5(tree)
        return tree

    scene.use_nodes = True
    return scene.node_tree


def _configure_blur_node(node, size_x: float, size_y: float):
    try:
        node.filter_type = 'GAUSS'
    except Exception:
        pass
    for attr, value in (
        ('use_relative', False),
        ('aspect_correction', 'NONE'),
        ('use_extended_bounds', True),
    ):
        if hasattr(node, attr):
            try:
                setattr(node, attr, value)
            except Exception:
                pass
    for attr, value in (
        ('size_x', size_x),
        ('size_y', size_y),
        ('factor_x', size_x),
        ('factor_y', size_y),
    ):
        if hasattr(node, attr):
            try:
                setattr(node, attr, value)
            except Exception:
                pass


def _socket_type(sock):
    return getattr(sock, 'type', '') or getattr(sock, 'bl_socket_idname', '')


def _socket_name(sock):
    return (getattr(sock, 'name', '') or '').lower()


def _find_socket(collection, names=None, socket_types=None, prefer_last=False):
    sockets = list(collection)
    if prefer_last:
        sockets = list(reversed(sockets))
    if names:
        names_lower = [n.lower() for n in names]
        for sock in sockets:
            n = _socket_name(sock)
            if any(key in n for key in names_lower):
                return sock
    if socket_types:
        for sock in sockets:
            st = _socket_type(sock)
            if st in socket_types or str(st).upper() in socket_types:
                return sock
    return sockets[-1] if prefer_last and sockets else (sockets[0] if sockets else None)


def _mix_input_sockets(node):
    inputs = list(node.inputs)
    fac = _find_socket(inputs, names=['fac', 'factor'])
    color_inputs = [s for s in inputs if _socket_type(s) in {'RGBA', 'NodeSocketColor', 'NodeSocketVector'}]
    if len(color_inputs) >= 2:
        return fac or inputs[0], color_inputs[0], color_inputs[1]
    if len(inputs) >= 3:
        return fac or inputs[0], inputs[-2], inputs[-1]
    raise RuntimeError(f'Unsupported mix node sockets: {node.bl_idname}')


def _mix_output_socket(node):
    color_output = _find_socket(node.outputs, socket_types={'RGBA', 'NodeSocketColor', 'NodeSocketVector'}, prefer_last=True)
    return color_output or node.outputs[0]


def _configure_mix_node(node, blend_type='MIX', fac=1.0):
    for attr, value in (
        ('data_type', 'RGBA'),
        ('factor_mode', 'UNIFORM'),
        ('blend_type', blend_type),
        ('use_clamp', False),
        ('clamp_result', False),
        ('clamp_factor', True),
    ):
        if hasattr(node, attr):
            try:
                setattr(node, attr, value)
            except Exception:
                pass
    fac_input, _, _ = _mix_input_sockets(node)
    try:
        fac_input.default_value = fac
    except Exception:
        pass


def _group_socket(group_node, name: str, fallback_index: int, collection_name: str):
    coll = getattr(group_node, collection_name)
    if hasattr(coll, 'get'):
        s = coll.get(name)
        if s is not None:
            return s
    return coll[fallback_index]


def _new_mix_node(nodes):
    # Blender 5 compositor node groups may not expose CompositorNodeMix / CompositorNodeMixRGB,
    # but ShaderNodeMix is often still available and its sockets are stable enough for our linking logic.
    return _new_supported(nodes, 'ShaderNodeMix', 'CompositorNodeMix', 'CompositorNodeMixRGB')


def _safe_link(links, from_socket, to_socket):
    if from_socket is None or to_socket is None:
        return
    try:
        links.new(from_socket, to_socket)
    except Exception:
        pass


def _ensure_gaussian_bloom_group() -> bpy.types.NodeTree:
    group = bpy.data.node_groups.get('SX_Bloom')
    if group is None or group.bl_idname != 'CompositorNodeTree':
        if group is not None:
            bpy.data.node_groups.remove(group)
        group = bpy.data.node_groups.new('SX_Bloom', 'CompositorNodeTree')

    group.use_fake_user = True
    nodes = group.nodes
    links = group.links
    nodes.clear()
    links.clear()
    _clear_interface(group)
    _add_interface_socket(group, '图像', 'INPUT', 'NodeSocketColor')
    _add_interface_socket(group, '图像', 'OUTPUT', 'NodeSocketColor')

    group_input = nodes.new('NodeGroupInput')
    group_input.location = (-1000, 0)
    group_output = nodes.new('NodeGroupOutput')
    group_output.location = (760, 0)

    blur_small = nodes.new('CompositorNodeBlur')
    blur_small.name = GLOW_NODE_NAMES['bloom_blur_small']
    blur_small.location = (-760, 240)
    _configure_blur_node(blur_small, 12.0, 12.0)

    blur_mid = nodes.new('CompositorNodeBlur')
    blur_mid.name = GLOW_NODE_NAMES['bloom_blur_mid']
    blur_mid.location = (-760, 20)
    _configure_blur_node(blur_mid, 36.0, 36.0)

    blur_large = nodes.new('CompositorNodeBlur')
    blur_large.name = GLOW_NODE_NAMES['bloom_blur_large']
    blur_large.location = (-760, -200)
    _configure_blur_node(blur_large, 92.0, 92.0)

    mix_small = _new_mix_node(nodes)
    mix_small.name = GLOW_NODE_NAMES['bloom_mix_small']
    mix_small.location = (-470, 240)
    _configure_mix_node(mix_small, 'MIX', 0.08)

    mix_mid = _new_mix_node(nodes)
    mix_mid.name = GLOW_NODE_NAMES['bloom_mix_mid']
    mix_mid.location = (-470, 20)
    _configure_mix_node(mix_mid, 'MIX', 0.14)

    mix_large = _new_mix_node(nodes)
    mix_large.name = GLOW_NODE_NAMES['bloom_mix_large']
    mix_large.location = (-470, -200)
    _configure_mix_node(mix_large, 'MIX', 0.20)

    add_a = _new_mix_node(nodes)
    add_a.name = GLOW_NODE_NAMES['bloom_add_a']
    add_a.location = (-120, 120)
    _configure_mix_node(add_a, 'ADD', 1.0)

    add_b = _new_mix_node(nodes)
    add_b.name = GLOW_NODE_NAMES['bloom_add_b']
    add_b.location = (150, 0)
    _configure_mix_node(add_b, 'ADD', 1.0)

    screen_mix = _new_mix_node(nodes)
    screen_mix.name = GLOW_NODE_NAMES['bloom_screen']
    screen_mix.location = (450, 0)
    _configure_mix_node(screen_mix, 'SCREEN', 0.10)

    input_socket = group_input.outputs[0]
    _safe_link(links, input_socket, blur_small.inputs[0])
    _safe_link(links, input_socket, blur_mid.inputs[0])
    _safe_link(links, input_socket, blur_large.inputs[0])

    _, mix_small_a, mix_small_b = _mix_input_sockets(mix_small)
    _, mix_mid_a, mix_mid_b = _mix_input_sockets(mix_mid)
    _, mix_large_a, mix_large_b = _mix_input_sockets(mix_large)
    _, add_a_a, add_a_b = _mix_input_sockets(add_a)
    _, add_b_a, add_b_b = _mix_input_sockets(add_b)
    _, screen_a, screen_b = _mix_input_sockets(screen_mix)

    _safe_link(links, input_socket, mix_small_a)
    _safe_link(links, blur_small.outputs[0], mix_small_b)
    _safe_link(links, input_socket, mix_mid_a)
    _safe_link(links, blur_mid.outputs[0], mix_mid_b)
    _safe_link(links, input_socket, mix_large_a)
    _safe_link(links, blur_large.outputs[0], mix_large_b)

    _safe_link(links, _mix_output_socket(mix_small), add_a_a)
    _safe_link(links, _mix_output_socket(mix_mid), add_a_b)
    _safe_link(links, _mix_output_socket(add_a), add_b_a)
    _safe_link(links, _mix_output_socket(mix_large), add_b_b)

    _safe_link(links, input_socket, screen_a)
    _safe_link(links, _mix_output_socket(add_b), screen_b)
    _safe_link(links, _mix_output_socket(screen_mix), group_output.inputs[0])

    return group


def _ensure_aces_tonemap_group() -> bpy.types.NodeTree:
    group = bpy.data.node_groups.get('SX_Tonemap')
    if group is None or group.bl_idname != 'CompositorNodeTree':
        if group is not None:
            bpy.data.node_groups.remove(group)
        group = bpy.data.node_groups.new('SX_Tonemap', 'CompositorNodeTree')

    group.use_fake_user = True
    nodes = group.nodes
    links = group.links
    nodes.clear()
    links.clear()
    _clear_interface(group)
    _add_interface_socket(group, '输入', 'INPUT', 'NodeSocketColor')
    _add_interface_socket(group, '图像', 'OUTPUT', 'NodeSocketColor')

    group_input = nodes.new('NodeGroupInput')
    group_input.location = (-700, 0)
    group_output = nodes.new('NodeGroupOutput')
    group_output.location = (380, 0)

    mix_a = _new_mix_node(nodes)
    mix_a.name = GLOW_NODE_NAMES['tonemap_mix_a']
    mix_a.location = (-360, 120)
    _configure_mix_node(mix_a, 'MIX', 0.015)

    mix_b = _new_mix_node(nodes)
    mix_b.name = GLOW_NODE_NAMES['tonemap_mix_b']
    mix_b.location = (-20, 0)
    _configure_mix_node(mix_b, 'MIX', 0.012)

    mix_out = _new_mix_node(nodes)
    mix_out.name = GLOW_NODE_NAMES['tonemap_mix_out']
    mix_out.location = (230, 0)
    _configure_mix_node(mix_out, 'ADD', 0.18)

    input_socket = group_input.outputs[0]
    _, mix_a_a, mix_a_b = _mix_input_sockets(mix_a)
    _, mix_b_a, mix_b_b = _mix_input_sockets(mix_b)
    _, mix_out_a, mix_out_b = _mix_input_sockets(mix_out)

    _safe_link(links, input_socket, mix_a_a)
    _safe_link(links, input_socket, mix_a_b)
    _safe_link(links, _mix_output_socket(mix_a), mix_b_a)
    _safe_link(links, input_socket, mix_b_b)
    _safe_link(links, _mix_output_socket(mix_b), mix_out_a)
    _safe_link(links, input_socket, mix_out_b)
    _safe_link(links, _mix_output_socket(mix_out), group_output.inputs[0])
    return group


def _ensure_anime_glow_group() -> bpy.types.NodeTree:
    group = bpy.data.node_groups.get(COMPOSITOR_GLOW_GROUP_NAME)
    if group is None or group.bl_idname != 'CompositorNodeTree':
        if group is not None:
            bpy.data.node_groups.remove(group)
        group = bpy.data.node_groups.new(COMPOSITOR_GLOW_GROUP_NAME, 'CompositorNodeTree')

    group.use_fake_user = True
    nodes = group.nodes
    links = group.links
    nodes.clear()
    links.clear()
    _clear_interface(group)
    _add_interface_socket(group, '图像', 'INPUT', 'NodeSocketColor')
    _add_interface_socket(group, '图像', 'OUTPUT', 'NodeSocketColor')

    group_input = nodes.new('NodeGroupInput')
    group_input.location = (-520, 0)
    group_output = nodes.new('NodeGroupOutput')
    group_output.location = (520, 0)

    gaussian = nodes.new('CompositorNodeGroup')
    gaussian.name = 'SX_Bloom'
    gaussian.label = 'SX_Bloom'
    gaussian.location = (-160, 0)
    gaussian.node_tree = _ensure_gaussian_bloom_group()

    tonemap = nodes.new('CompositorNodeGroup')
    tonemap.name = 'SX_Tonemap'
    tonemap.label = 'SX_Tonemap'
    tonemap.location = (180, 0)
    tonemap.node_tree = _ensure_aces_tonemap_group()

    _safe_link(links, group_input.outputs[0], _group_socket(gaussian, '图像', 0, 'inputs'))
    _safe_link(links, _group_socket(gaussian, '图像', 0, 'outputs'), _group_socket(tonemap, '输入', 0, 'inputs'))
    _safe_link(links, _group_socket(tonemap, '图像', 0, 'outputs'), group_output.inputs[0])
    return group


def _threshold_to_strengths(threshold: float):
    t = max(0.0, min(10.0, float(threshold)))
    strength = max(0.0, min(1.0, (1.2 - t) / 1.2))
    small = max(0.0, min(1.0, 0.02 + strength * 0.10))
    mid = max(0.0, min(1.0, 0.04 + strength * 0.12))
    large = max(0.0, min(1.0, 0.06 + strength * 0.14))
    screen = max(0.0, min(1.0, 0.04 + strength * 0.08))
    return small, mid, large, screen


def _apply_threshold_to_group_node(node, threshold: float):
    tree = getattr(node, 'node_tree', None)
    if tree is None:
        return
    small, mid, large, screen = _threshold_to_strengths(threshold)

    gaussian = tree.nodes.get('SX_Bloom')
    if gaussian and getattr(gaussian, 'node_tree', None):
        bloom_tree = gaussian.node_tree
        value_map = {
            GLOW_NODE_NAMES['bloom_mix_small']: small,
            GLOW_NODE_NAMES['bloom_mix_mid']: mid,
            GLOW_NODE_NAMES['bloom_mix_large']: large,
            GLOW_NODE_NAMES['bloom_screen']: screen,
        }
        for name, value in value_map.items():
            n = bloom_tree.nodes.get(name)
            if n:
                fac_input, _, _ = _mix_input_sockets(n)
                try:
                    fac_input.default_value = value
                except Exception:
                    pass

        blur_map = {
            GLOW_NODE_NAMES['bloom_blur_small']: 8.0 + (1.0 - small) * 10.0,
            GLOW_NODE_NAMES['bloom_blur_mid']: 24.0 + (1.0 - mid) * 22.0,
            GLOW_NODE_NAMES['bloom_blur_large']: 60.0 + (1.0 - large) * 40.0,
        }
        for name, size in blur_map.items():
            n = bloom_tree.nodes.get(name)
            if n:
                _configure_blur_node(n, size, size)


def _ensure_group_node(tree, threshold: float):
    node = tree.nodes.get(COMPOSITOR_GLOW_GROUP_NODE_NAME)
    if node is None or node.bl_idname != 'CompositorNodeGroup':
        if node is not None:
            tree.nodes.remove(node)
        node = tree.nodes.new('CompositorNodeGroup')
        node.name = COMPOSITOR_GLOW_GROUP_NODE_NAME

    node.node_tree = _ensure_anime_glow_group()
    node.location = (-40, 0)
    node["sx_compositor_node"] = True
    _apply_threshold_to_group_node(node, threshold)
    return node


def ensure_glow_setup(scene, threshold: float):
    try:
        scene.render.use_compositing = True
    except Exception:
        pass

    tree = get_or_create_compositor_tree(scene)
    links = tree.links

    for node in list(tree.nodes):
        if node.bl_idname in {'CompositorNodeViewer', 'CompositorNodeComposite', 'NodeGroupOutput'}:
            tree.nodes.remove(node)

    render_layers = _find_or_create(tree, 'CompositorNodeRLayers', COMPOSITOR_RLAYERS_NAME, (-350, 0))
    glow_node = _ensure_group_node(tree, threshold)

    if _is_blender_5_compositor(scene):
        output = _find_or_create(tree, 'NodeGroupOutput', COMPOSITOR_COMPOSITE_NAME, (280, 40))
    else:
        output = _find_or_create(tree, 'CompositorNodeComposite', COMPOSITOR_COMPOSITE_NAME, (280, 40))

    viewer = _find_or_create(tree, 'CompositorNodeViewer', COMPOSITOR_VIEWER_NAME, (280, -100))

    for node in (glow_node, output, viewer):
        for socket in getattr(node, 'inputs', []):
            for link in list(socket.links):
                links.remove(link)

    for socket in getattr(render_layers, 'outputs', []):
        for link in list(socket.links):
            links.remove(link)

    image_input = glow_node.inputs.get('图像') if hasattr(glow_node.inputs, 'get') and glow_node.inputs.get('图像') else glow_node.inputs[0]
    image_output = glow_node.outputs.get('图像') if hasattr(glow_node.outputs, 'get') and glow_node.outputs.get('图像') else glow_node.outputs[0]
    links.new(render_layers.outputs['Image'], image_input)
    links.new(image_output, output.inputs[0])
    links.new(image_output, viewer.inputs['Image'])

    scene[COMPOSITOR_TREE_FLAG] = True


def remove_glow_setup(scene) -> bool:
    tree = get_or_create_compositor_tree(scene)
    if not tree:
        return False

    removed = False
    for name in [
        COMPOSITOR_GLOW_GROUP_NODE_NAME,
        COMPOSITOR_VIEWER_NAME,
        'SX_Glare',
        'Paper_Glare',
        'Paper_RGB_Curves',
    ]:
        node = tree.nodes.get(name)
        if node:
            tree.nodes.remove(node)
            removed = True

    render_layers = tree.nodes.get(COMPOSITOR_RLAYERS_NAME)
    output = tree.nodes.get(COMPOSITOR_COMPOSITE_NAME)
    if render_layers and output:
        for socket in output.inputs:
            for link in list(socket.links):
                tree.links.remove(link)
        tree.links.new(render_layers.outputs['Image'], output.inputs[0])
        removed = True

    if COMPOSITOR_TREE_FLAG in scene:
        del scene[COMPOSITOR_TREE_FLAG]
    return removed


def update_glow_setup(scene, threshold: float):
    tree = get_or_create_compositor_tree(scene)
    if not tree:
        return
    node = tree.nodes.get(COMPOSITOR_GLOW_GROUP_NODE_NAME)
    if not node:
        return
    _apply_threshold_to_group_node(node, threshold)
