import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r109-scalp-density-texture-r123-sweep"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
VARIANTS = (
    ("a-control", None),
    ("b-broad-80", {"scale": 80.0, "minimum": 0.58}),
    ("c-balanced-180", {"scale": 180.0, "minimum": 0.34}),
    ("d-fine-360", {"scale": 360.0, "minimum": 0.18}),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def find_nodes(material):
    principled = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    density = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeMath")
    return principled, density


def apply_settings(settings):
    scalp = bpy.data.objects[SCALP]
    material = scalp.data.materials[0]
    principled, density = find_nodes(material)
    if settings is not None:
        tree = material.node_tree
        alpha_link = next(link for link in tree.links if link.to_node == principled and link.to_socket.name == "Alpha")
        tree.links.remove(alpha_link)
        coordinates = tree.nodes.new("ShaderNodeTexCoord")
        coordinates.name = "Aevrynd Scalp Coordinates v249r123"
        noise = tree.nodes.new("ShaderNodeTexNoise")
        noise.name = "Aevrynd Root Density Noise v249r123"
        noise.noise_dimensions = "3D"
        noise.inputs["Scale"].default_value = settings["scale"]
        noise.inputs["Detail"].default_value = 2.4
        noise.inputs["Roughness"].default_value = 0.62
        remap = tree.nodes.new("ShaderNodeMapRange")
        remap.name = "Aevrynd Root Density Remap v249r123"
        remap.clamp = True
        remap.inputs["From Min"].default_value = 0.24
        remap.inputs["From Max"].default_value = 0.76
        remap.inputs["To Min"].default_value = settings["minimum"]
        remap.inputs["To Max"].default_value = 1.0
        combine = tree.nodes.new("ShaderNodeMath")
        combine.name = "Aevrynd Textured Density v249r123"
        combine.operation = "MULTIPLY"
        tree.links.new(coordinates.outputs["Generated"], noise.inputs["Vector"])
        tree.links.new(noise.outputs["Fac"], remap.inputs["Value"])
        tree.links.new(density.outputs[0], combine.inputs[0])
        tree.links.new(remap.outputs["Result"], combine.inputs[1])
        tree.links.new(combine.outputs[0], principled.inputs["Alpha"])
    return {
        "baseColor": list(principled.inputs["Base Color"].default_value),
        "densityStrength": float(density.inputs[1].default_value),
        "roughness": float(principled.inputs["Roughness"].default_value),
        "specularIorLevel": float(principled.inputs["Specular IOR Level"].default_value),
        "noiseScale": settings["scale"] if settings else 0.0,
        "noiseMinimum": settings["minimum"] if settings else 1.0,
    }


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": []}
for name, settings in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    applied = apply_settings(settings)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for suffix, location, target, lens in (
        ("01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({"name": name, **applied})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_SCALP_DENSITY_TEXTURE_R123=" + json.dumps(report, sort_keys=True))
