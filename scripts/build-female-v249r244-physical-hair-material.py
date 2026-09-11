import hashlib
import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-baked-root-veil-r241.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-physical-hair-r244.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-physical-hair-r244.build-report.json"


def hair_objects():
    return [obj for obj in bpy.context.scene.objects if obj.type == "CURVES" and bool(obj.get("aevrynd_mainline_hair_collision"))]


def geometry_hash(obj):
    digest = hashlib.sha256()
    for curve in obj.data.curves:
        digest.update(int(curve.points_length).to_bytes(4, "little"))
    for point in obj.data.points:
        for value in point.position:
            digest.update(float(value).hex().encode("ascii"))
    return digest.hexdigest()


def make_material(name, melanin, redness, roughness, radial, variation):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfHairPrincipled")
    shader.parametrization = "MELANIN"
    shader.inputs["Melanin"].default_value = melanin
    shader.inputs["Melanin Redness"].default_value = redness
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Radial Roughness"].default_value = radial
    shader.inputs["Coat"].default_value = 0.05
    shader.inputs["IOR"].default_value = 1.55
    shader.inputs["Random Color"].default_value = variation
    shader.inputs["Random Roughness"].default_value = 0.07
    links.new(shader.outputs[0], output.inputs["Surface"])
    material["aevrynd_revision"] = "v249r244-physical-hair"
    material["aevrynd_runtime_dependency"] = "none"
    return material


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
objects = hair_objects()
before = {obj.name: geometry_hash(obj) for obj in objects}
base = make_material("AevryndFemaleHairBase_v249r244", 0.82, 0.28, 0.46, 0.34, 0.10)
overlay = make_material("AevryndFemaleHairOverlay_v249r244", 0.74, 0.34, 0.42, 0.30, 0.16)
assignments = {}
for obj in objects:
    material = overlay if "overlay" in str(obj.get("aevrynd_layer", "")) else base
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj["aevrynd_revision"] = "v249r244-physical-hair"
    obj["aevrynd_hair_shading"] = "dual Principled Hair BSDF melanin layers"
    assignments[obj.name] = material.name
after = {obj.name: geometry_hash(obj) for obj in objects}

scene = bpy.context.scene
scene["aevrynd_mainline_revision"] = "v249r244-physical-hair"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_runtime_dependency"] = "none"
scene["aevrynd_release_state"] = "COLLISION_PARITY_AND_11SHOT_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "materials": {
        "base": {"name": base.name, "melanin": 0.82, "redness": 0.28, "roughness": 0.46, "radialRoughness": 0.34},
        "overlay": {"name": overlay.name, "melanin": 0.74, "redness": 0.34, "roughness": 0.42, "radialRoughness": 0.30},
    },
    "assignments": assignments,
    "geometryParity": before == after,
    "before": before,
    "after": after,
    "runtimeDependency": "none",
    "status": "COLLISION_PARITY_AND_11SHOT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R244_PHYSICAL_HAIR=" + json.dumps(report, sort_keys=True))
