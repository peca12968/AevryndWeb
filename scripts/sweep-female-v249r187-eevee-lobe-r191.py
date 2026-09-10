import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-anatomical-hairline-fade-r187.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r191-eevee-lobe-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eevee-lobe-r191.sweep-report.json"
MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
HAIR_OBJECTS = (
    "AevryndFemaleCC0LongHairStudyMain_v249r85",
    "AevryndFemaleCC0LongHairStudyFlyaway_v249r85",
)
VARIANTS = (
    {"name": "a-control", "control": True},
    {"name": "b-satin", "metallic": 0.62, "roughness": 0.58, "sss": 0.18, "specular": 0.28, "anisotropic": 0.42, "coat": 0.025},
    {"name": "c-balanced-dry", "metallic": 0.48, "roughness": 0.64, "sss": 0.08, "specular": 0.24, "anisotropic": 0.52, "coat": 0.018},
    {"name": "d-low-sheen", "metallic": 0.34, "roughness": 0.69, "sss": 0.03, "specular": 0.20, "anisotropic": 0.60, "coat": 0.012},
)


def tuned_material(base, variant):
    material = base.copy()
    material.name = "AevryndOwnedEeveeLobeStudy_v249r191_" + variant["name"]
    group = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeGroup")
    group.node_tree = group.node_tree.copy()
    tree = group.node_tree
    shader = next(node for node in tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    for socket_name in ("Coat Weight", "Coat Roughness"):
        for link in list(shader.inputs[socket_name].links):
            tree.links.remove(link)
    shader.inputs["Metallic"].default_value = variant["metallic"]
    shader.inputs["Roughness"].default_value = variant["roughness"]
    shader.inputs["Subsurface Weight"].default_value = variant["sss"]
    shader.inputs["Subsurface Scale"].default_value = 0.002
    shader.inputs["Specular IOR Level"].default_value = variant["specular"]
    shader.inputs["Anisotropic"].default_value = variant["anisotropic"]
    shader.inputs["Coat Weight"].default_value = variant["coat"]
    shader.inputs["Coat Roughness"].default_value = 0.48
    material["aevrynd_revision"] = "v249r191"
    material["aevrynd_study"] = variant["name"]
    return material


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "geometryChanged": False, "variants": []}
for variant in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    base = bpy.data.materials[MATERIAL]
    material = base if variant.get("control") else tuned_material(base, variant)
    for object_name in HAIR_OBJECTS:
        obj = bpy.data.objects[object_name]
        obj.data.materials.clear()
        obj.data.materials.append(material)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-hair-back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.60), 88),
        ("04-hair-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    )
    for view_name, location, target, lens in views:
        render(camera, f"{variant['name']}-{view_name}.png", location, target, lens)
    report["variants"].append(variant)

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R191_EEVEE_LOBE=" + json.dumps(report, sort_keys=True))
