import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OFFICIAL = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-owned-hair-material-r129.build.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLYAWAY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
COLOR_1 = (0.033, 0.014, 0.005, 1.0)
COLOR_2 = (0.007, 0.0025, 0.001, 1.0)
RANDOM_COLOR = 0.45
SCALP_DENSITY = 0.42


def import_official_material():
    with bpy.data.libraries.load(str(OFFICIAL), link=False) as (source, target):
        if "Brown hair" not in source.materials:
            raise RuntimeError("official Brown hair material missing")
        target.materials = ["Brown hair"]
    return target.materials[0]


def radius_range(obj):
    radius = obj.data.attributes.get("radius")
    values = [float(item.value) for item in radius.data] if radius else []
    return [min(values) * 1.0e6, max(values) * 1.0e6] if values else None


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
material = import_official_material()
material.name = "AevryndOwnedLayeredHairMaterial_v249r129"
material["aevrynd_layer"] = "hair.material.layered"
material["aevrynd_revision"] = "v249r129"
material["aevrynd_source"] = "Blender official Hair Nodes female hair styles; CC0 material node group copied and recolored offline"
material["aevrynd_license"] = "CC0"
material["aevrynd_runtime_dependency"] = "none"
group = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeGroup")
group.inputs["Color 1"].default_value = COLOR_1
group.inputs["Color 2"].default_value = COLOR_2
group.inputs["Darken root"].default_value = 0.6313559412956238
group.inputs["Root color length"].default_value = 0.3220338821411133
group.inputs["Random color"].default_value = RANDOM_COLOR
group.inputs["Noise Scale"].default_value = 18.8

for name in (MAIN, FLYAWAY):
    obj = bpy.data.objects[name]
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj["aevrynd_material_revision"] = "v249r129"
    obj["aevrynd_material_source"] = "Aevrynd-owned CC0 layered hair derivative"

scalp = bpy.data.objects[SCALP]
scalp_material = scalp.data.materials[0].copy()
scalp_material.name = "AevryndAnatomicalScalpFoundationMaterial_v249r129"
principled = next(node for node in scalp_material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
density = next(node for node in scalp_material.node_tree.nodes if node.bl_idname == "ShaderNodeMath")
principled.inputs["Base Color"].default_value = COLOR_2
principled.inputs["Roughness"].default_value = 0.94
principled.inputs["Specular IOR Level"].default_value = 0.05
density.inputs[1].default_value = SCALP_DENSITY
scalp.data.materials.clear()
scalp.data.materials.append(scalp_material)
scalp["aevrynd_material_revision"] = "v249r129"

scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "owned-hair-material-r129"
scene["aevrynd_release_state"] = "R129_VISUAL_COLLISION_DYNAMIC_PERFORMANCE_REVIEW_REQUIRED"
scene["aevrynd_runtime_dependency"] = "none"

report = {
    "source": str(SOURCE),
    "officialMaterialSource": str(OFFICIAL),
    "output": str(OUTPUT),
    "license": "CC0",
    "runtimeDependency": "none",
    "material": material.name,
    "color1": list(COLOR_1),
    "color2": list(COLOR_2),
    "randomColor": RANDOM_COLOR,
    "darkenRoot": float(group.inputs["Darken root"].default_value),
    "rootColorLength": float(group.inputs["Root color length"].default_value),
    "noiseScale": float(group.inputs["Noise Scale"].default_value),
    "scalpDensity": SCALP_DENSITY,
    "mainRadiusUm": radius_range(bpy.data.objects[MAIN]),
    "flyawayRadiusUm": radius_range(bpy.data.objects[FLYAWAY]),
    "geometryChanged": False,
    "status": "VISUAL_COLLISION_DYNAMIC_PERFORMANCE_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_OWNED_DEEP_BROWN_HAIR_R129=" + json.dumps(report, sort_keys=True))
