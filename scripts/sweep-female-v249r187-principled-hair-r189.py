import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-anatomical-hairline-fade-r187.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r189-principled-hair-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-principled-hair-r189.sweep-report.json"
MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
HAIR_OBJECTS = (
    "AevryndFemaleCC0LongHairStudyMain_v249r85",
    "AevryndFemaleCC0LongHairStudyFlyaway_v249r85",
)
VARIANTS = (
    {"name": "a-control", "control": True},
    {"name": "b-hair-balanced", "roughness": 0.38, "radial": 0.48, "coat": 0.08, "random_roughness": 0.08},
    {"name": "c-hair-soft", "roughness": 0.48, "radial": 0.58, "coat": 0.04, "random_roughness": 0.13},
    {"name": "d-hair-dry", "roughness": 0.58, "radial": 0.68, "coat": 0.02, "random_roughness": 0.18},
)


def set_input(node, name, value):
    socket = node.inputs.get(name)
    if socket is None:
        raise RuntimeError(f"missing {node.name}.{name}")
    socket.default_value = value


def tuned_material(base, variant):
    material = base.copy()
    material.name = "AevryndOwnedPrincipledHairStudy_v249r189_" + variant["name"]
    group = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeGroup")
    group.node_tree = group.node_tree.copy()
    tree = group.node_tree
    output = next(node for node in tree.nodes if node.bl_idname == "NodeGroupOutput")
    eevee = output.inputs.get("EEVEE Shader")
    if eevee is None:
        raise RuntimeError("official group has no EEVEE Shader output")
    for link in list(tree.links):
        if link.to_socket == eevee:
            tree.links.remove(link)
    shader = tree.nodes.new("ShaderNodeBsdfHairPrincipled")
    shader.name = "Aevrynd Principled Hair r189"
    shader.parametrization = "COLOR"
    set_input(shader, "Color", (0.028, 0.0105, 0.0035, 1.0))
    set_input(shader, "Roughness", variant["roughness"])
    set_input(shader, "Radial Roughness", variant["radial"])
    set_input(shader, "Coat", variant["coat"])
    set_input(shader, "IOR", 1.55)
    if shader.inputs.get("Random Color"):
        set_input(shader, "Random Color", 0.12)
    if shader.inputs.get("Random Roughness"):
        set_input(shader, "Random Roughness", variant["random_roughness"])
    tree.links.new(shader.outputs[0], eevee)
    material["aevrynd_revision"] = "v249r189"
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
print("AEVRYND_V249R189_PRINCIPLED_HAIR=" + json.dumps(report, sort_keys=True))
