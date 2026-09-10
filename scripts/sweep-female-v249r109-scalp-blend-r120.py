import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r109-scalp-blend-r120-sweep"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
VARIANTS = (
    ("a-control", None),
    ("b-low-spec", {"color": (0.0120, 0.0028, 0.0012, 1.0), "density": 0.50, "roughness": 0.94, "specular": 0.05}),
    ("c-warm-soft", {"color": (0.0260, 0.0070, 0.0030, 1.0), "density": 0.42, "roughness": 0.94, "specular": 0.05}),
    ("d-warm-dense", {"color": (0.0260, 0.0070, 0.0030, 1.0), "density": 0.62, "roughness": 0.94, "specular": 0.05}),
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
        principled.inputs["Base Color"].default_value = settings["color"]
        principled.inputs["Roughness"].default_value = settings["roughness"]
        principled.inputs["Specular IOR Level"].default_value = settings["specular"]
        density.inputs[1].default_value = settings["density"]
    return {
        "baseColor": list(principled.inputs["Base Color"].default_value),
        "densityStrength": float(density.inputs[1].default_value),
        "roughness": float(principled.inputs["Roughness"].default_value),
        "specularIorLevel": float(principled.inputs["Specular IOR Level"].default_value),
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
print("AEVRYND_SCALP_BLEND_R120=" + json.dumps(report, sort_keys=True))
