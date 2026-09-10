import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-satin-hair-r192.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r195-brow-density-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-brow-density-r195.sweep-report.json"
VARIANTS = (
    {"name": "a-control", "control": True},
    {"name": "b-subtle", "fiberAlpha": 0.67, "densityGain": 1.12},
    {"name": "c-balanced", "fiberAlpha": 0.76, "densityGain": 1.28},
    {"name": "d-strong", "fiberAlpha": 0.86, "densityGain": 1.45},
)


def principled(material):
    return next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")


def tuned_fiber(source, name, alpha):
    material = source.copy()
    material.name = name
    shader = principled(material)
    shader.inputs["Alpha"].default_value = alpha
    shader.inputs["Roughness"].default_value = 0.58
    material["aevrynd_revision"] = "v249r195"
    return material


def tuned_density(source, name, gain):
    material = source.copy()
    material.name = name
    tree = material.node_tree
    shader = principled(material)
    alpha = shader.inputs["Alpha"]
    incoming = alpha.links[0]
    source_socket = incoming.from_socket
    tree.links.remove(incoming)
    multiply = tree.nodes.new("ShaderNodeMath")
    multiply.name = "Aevrynd Brow Density Gain r195"
    multiply.operation = "MULTIPLY"
    multiply.use_clamp = True
    multiply.inputs[1].default_value = gain
    tree.links.new(source_socket, multiply.inputs[0])
    tree.links.new(multiply.outputs[0], alpha)
    shader.inputs["Roughness"].default_value = 0.72
    material["aevrynd_revision"] = "v249r195"
    return material


def apply_variant(variant):
    if variant.get("control"):
        return
    dark = tuned_fiber(bpy.data.materials["Aevrynd_Brow_Hair_v39_Dark"], "Aevrynd_Brow_Hair_R195_Dark_" + variant["name"], variant["fiberAlpha"])
    warm = tuned_fiber(bpy.data.materials["Aevrynd_Brow_Hair_v39_Warm"], "Aevrynd_Brow_Hair_R195_Warm_" + variant["name"], variant["fiberAlpha"])
    density = tuned_density(bpy.data.materials["Aevrynd_Brow_Density_v39"], "Aevrynd_Brow_Density_R195_" + variant["name"], variant["densityGain"])
    for side in ("L", "R"):
        brow = bpy.data.objects[f"Brow_{side}"]
        brow.data.materials.clear()
        brow.data.materials.append(dark)
        brow.data.materials.append(warm)
        density_obj = bpy.data.objects[f"Brow_{side}_Density"]
        density_obj.data.materials.clear()
        density_obj.data.materials.append(density)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens, size):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "geometryChanged": False, "variants": []}
for variant in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    apply_variant(variant)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-brows-front", (0.0, -0.445, 1.627), (0.0, -0.076, 1.622), 132, (1280, 760)),
        ("02-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
        ("03-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88, (1000, 1000)),
    )
    for view_name, location, target, lens, size in views:
        render(camera, f"{variant['name']}-{view_name}.png", location, target, lens, size)
    report["variants"].append(variant)

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R195_BROW_DENSITY=" + json.dumps(report, sort_keys=True))
