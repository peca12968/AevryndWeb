import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-baked-root-veil-r241.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r242-principled-hair-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-principled-hair-r242.sweep-report.json"
VARIANTS = (
    ("a-control", None),
    ("b-melanin-balanced", {"melanin": 0.82, "redness": 0.28, "roughness": 0.46, "radial": 0.34}),
    ("c-melanin-dark", {"melanin": 0.92, "redness": 0.18, "roughness": 0.50, "radial": 0.38}),
    ("d-melanin-soft", {"melanin": 0.86, "redness": 0.34, "roughness": 0.58, "radial": 0.44}),
)


def hair_objects():
    return [
        obj for obj in bpy.context.scene.objects
        if obj.type == "CURVES" and bool(obj.get("aevrynd_mainline_hair_collision"))
    ]


def make_material(name, settings):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfHairPrincipled")
    shader.parametrization = "MELANIN"
    shader.inputs["Melanin"].default_value = settings["melanin"]
    shader.inputs["Melanin Redness"].default_value = settings["redness"]
    shader.inputs["Roughness"].default_value = settings["roughness"]
    shader.inputs["Radial Roughness"].default_value = settings["radial"]
    shader.inputs["Coat"].default_value = 0.06
    shader.inputs["IOR"].default_value = 1.55
    shader.inputs["Random Color"].default_value = 0.12
    shader.inputs["Random Roughness"].default_value = 0.08
    links.new(shader.outputs[0], output.inputs["Surface"])
    material["aevrynd_revision"] = "v249r242-principled-hair-study"
    return material


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "geometryChanged": False, "variants": {}}
for label, settings in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    objects = hair_objects()
    material = None
    if settings is not None:
        material = make_material(f"AevryndFemalePrincipledHair_{label}_v249r242", settings)
        for obj in objects:
            obj.data.materials.clear()
            obj.data.materials.append(material)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for view_name, location, target, lens in (
        ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.595), 88),
        ("04-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(camera, f"{label}-{view_name}.png", location, target, lens)
    report["variants"][label] = {
        "settings": settings or "r241-control",
        "material": material.name if material else "existing per-layer materials",
        "objects": len(objects),
    }
report["status"] = "STRICT_VISUAL_SELECTION_PENDING"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R242_PRINCIPLED_HAIR=" + json.dumps(report, sort_keys=True))
