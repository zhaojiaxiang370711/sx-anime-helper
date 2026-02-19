bl_info = {
    "name": "Paper朱二次元助手（强化版）",
    "author": "Paper朱 + ChatGPT",
    "version": (3, 1, 0),
    "blender": (5, 0, 1),
    "location": "View3D / Shader Editor N 面板：Paper二分；材质属性面板：Paper朱 高光皮肤材质",
    "description": "一键描边 + 高光皮肤（Skin_shiny风格）+ 单材质槽处理 + Matcap + 色彩管理",
    "category": "Material",
}

import importlib
from . import (
    props,
    utils_engine,
    constants,
    materials,
    ops_outline,
    ops_color,
    ops_skin,
    ops_slot_replace,
    ui_view3d,
    ui_shader,
    ui_material_panel,
)

modules = (
    props,
    utils_engine,
    constants,
    materials,
    ops_outline,
    ops_color,
    ops_skin,
    ops_slot_replace,
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
