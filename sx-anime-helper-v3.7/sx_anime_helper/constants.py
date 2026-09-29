# Paper said：ciallo
ADDON_CATEGORY = "SX Anime"
TAG = "SX_SKIN_SHINY"

OUTLINE_MATERIAL_NAME = "SX_Outline_Black"
OUTLINE_MODIFIER_NAME = "SX_Outline_Solidify"
OUTLINE_MATERIAL_FLAG = "sx_is_outline_material"

SKIN_REROUTE_NAME = "SX_OrigBaseColor"
SKIN_FINAL_MIX_NAME = "SX_FinalMix"
SKIN_GLOSSY_NAME = "SX_Glossy"
SKIN_RAMP_LIGHT_NAME = "SX_Ramp_LightMask"
SKIN_RAMP_HIGHLIGHT_NAME = "SX_Ramp_HighlightMask"
SKIN_EDGE_RAMP_NAME = "SX_Ramp_EdgeMask"
SKIN_MATCAP_ADD_NAME = "SX_AddMatcap"

COMPOSITOR_TREE_FLAG = "sx_glow_setup"
COMPOSITOR_GLOW_GROUP_NAME = "SX_Anime_Glow"
COMPOSITOR_GLOW_GROUP_NODE_NAME = "SX_Anime_Glow"
COMPOSITOR_VIEWER_NAME = "SX_Viewer"
COMPOSITOR_COMPOSITE_NAME = "SX_Composite"
COMPOSITOR_RLAYERS_NAME = "SX_RenderLayers"

COLOR_LOOK_PRESETS = [
    ('MEDIUM_HIGH', '中高对比', 'Standard + Medium High Contrast'),
    ('AGX_HIGH', 'AGX高对比', 'AgX + High Contrast'),
    ('NONE', '无', '不使用额外对比度预设'),
    ('HIGH', '高对比', 'High Contrast'),
    ('VERY_HIGH', '极高对比', 'Very High Contrast'),
]

COLOR_LOOK_MAP = {
    'AGX_HIGH': 'High Contrast',
    'NONE': 'None',
    'MEDIUM_HIGH': 'Medium High Contrast',
    'HIGH': 'High Contrast',
    'VERY_HIGH': 'Very High Contrast',
}
