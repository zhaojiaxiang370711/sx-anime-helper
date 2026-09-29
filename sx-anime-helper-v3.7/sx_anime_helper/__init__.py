# Paper said：ciallo
bl_info = {
    "name": "SX Anime Helper",
    "author": "Paper朱 + ChatGPT",
    "version": (3, 7, 1),
    "blender": (4, 1, 0),
    "location": "View3D / Shader Editor N panel: SX Anime; Material properties: SX Anime Skin Highlight",
    "description": "One-click outline (adjustable/fix/remove) + toon highlight skin (Matcap) + per-slot processing + color management + one-click glow",
    "category": "Material",
}

import importlib
from . import (
    constants,
    utils,
    materials,
    compositor,
    props,
    ops_outline,
    ops_color,
    ops_skin,
    ops_slot_replace,
    ops_glow,
    ui_view3d,
    ui_shader,
    ui_material_panel,
)

modules = (
    constants,
    utils,
    materials,
    compositor,
    props,
    ops_outline,
    ops_color,
    ops_skin,
    ops_slot_replace,
    ops_glow,
    ui_view3d,
    ui_shader,
    ui_material_panel,
)


def register():
    for m in modules:
        importlib.reload(m)
    for m in modules:
        if hasattr(m, "register"):
            m.register()


def unregister():
    for m in reversed(modules):
        if hasattr(m, "unregister"):
            m.unregister()
