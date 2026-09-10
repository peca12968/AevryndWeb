import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-crown-clump-coverage-r166.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r166-eevee-hair-hybrid-r168-sweep"
BASE_MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
HAIR_OBJECTS = (
    "AevryndFemaleOwnedCurlyHairMain_v249r162",
    "AevryndFemaleOwnedCurlyCrownClumps_v249r166",
)
VARIANTS = (
    {"name": "control", "control": True},
    {"name": "metal25-rough42", "metallic": 0.25, "roughness": 0.42},
    {"name": "metal45-rough50", "metallic": 0.45, "roughness": 0.50},
    {"name": "metal60-rough58", "metallic": 0.60, "roughness": 0.58},
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def tuned_material(base, variant):
    material = base.copy()
    material.name = "AevryndOwnedEeveeHairHybridStudy_v249r168_" + variant["name"]
    group = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeGroup")
    group.node_tree = group.node_tree.copy()
    tree = group.node_tree
    principled = next(node for node in tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    for socket_name in ("Coat Weight", "Coat Roughness"):
        socket = principled.inputs[socket_name]
        for link in list(socket.links):
            tree.links.remove(link)
    principled.inputs["Metallic"].default_value = variant["metallic"]
    principled.inputs["Roughness"].default_value = variant["roughness"]
    principled.inputs["IOR"].default_value = 1.45
    principled.inputs["Subsurface Weight"].default_value = 0.0
    principled.inputs["Specular IOR Level"].default_value = 0.25
    principled.inputs["Anisotropic"].default_value = 0.42
    principled.inputs["Coat Weight"].default_value = 0.03
    principled.inputs["Coat Roughness"].default_value = 0.40
    material["aevrynd_revision"] = "v249r168"
    material["aevrynd_study"] = variant["name"]
    return material


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
base = bpy.data.materials[BASE_MATERIAL]
report = {"source": str(SOURCE), "variants": [], "status": "STRICT_VISUAL_REVIEW_REQUIRED"}
for variant in VARIANTS:
    material = base if variant.get("control") else tuned_material(base, variant)
    for object_name in HAIR_OBJECTS:
        obj = bpy.data.objects[object_name]
        obj.data.materials.clear()
        obj.data.materials.append(material)
    render(camera, variant["name"] + "-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
    render(camera, variant["name"] + "-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
    render(camera, variant["name"] + "-profile", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88)
    render(camera, variant["name"] + "-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78)
    report["variants"].append(variant)
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R168_HYBRID_SWEEP=" + json.dumps(report, sort_keys=True))
