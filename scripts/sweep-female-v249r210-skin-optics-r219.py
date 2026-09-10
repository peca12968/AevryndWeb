import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r219-skin-optics-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-skin-optics-r219.sweep-report.json"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (
    ("a-control", None),
    ("b-readable-dry", {"roughnessScale": 0.92, "sssWeight": 0.025, "sssScale": 0.0014, "specular": 0.24, "bump": 0.15, "coat": 0.010}),
    ("c-balanced", {"roughnessScale": 0.82, "sssWeight": 0.055, "sssScale": 0.0016, "specular": 0.28, "bump": 0.145, "coat": 0.016}),
    ("d-cinematic", {"roughnessScale": 0.72, "sssWeight": 0.085, "sssScale": 0.0018, "specular": 0.32, "bump": 0.16, "coat": 0.024}),
)


def tune_material(body, settings, label):
    material = body.active_material.copy()
    material.name = f"Aevrynd_Skin_Optics_R219_{label}"
    body.data.materials.clear()
    body.data.materials.append(material)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")

    roughness = shader.inputs["Roughness"]
    if roughness.links:
        source = roughness.links[0].from_socket
        for link in list(roughness.links):
            links.remove(link)
        scale = nodes.new("ShaderNodeMath")
        scale.name = f"Aevrynd Roughness Scale R219 {label}"
        scale.operation = "MULTIPLY"
        scale.inputs[1].default_value = settings["roughnessScale"]
        links.new(source, scale.inputs[0])
        links.new(scale.outputs[0], roughness)

    shader.inputs["Subsurface Weight"].default_value = settings["sssWeight"]
    shader.inputs["Subsurface Scale"].default_value = settings["sssScale"]
    shader.inputs["Subsurface Radius"].default_value = (1.0, 0.32, 0.16)
    shader.inputs["Specular IOR Level"].default_value = settings["specular"]
    shader.inputs["Coat Weight"].default_value = settings["coat"]
    shader.inputs["Coat Roughness"].default_value = 0.34
    bump = nodes.get("Aevrynd Dual Scale Skin Bump v249r173")
    if bump:
        bump.inputs["Strength"].default_value = settings["bump"]
    material["aevrynd_skin_revision"] = "v249r219-sweep"
    material["aevrynd_skin_optics_variant"] = label
    return material.name


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
report = {"source": str(SOURCE), "variants": {}, "status": "VISUAL_SELECTION_PENDING"}
for label, settings in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    body = bpy.data.objects[BODY]
    material = body.active_material.name if settings is None else tune_material(body, settings, label)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-face-front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108),
        ("02-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-face-profile", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88),
        ("04-skin-close", (0.0, -0.43, 1.585), (0.0, -0.082, 1.585), 120),
    )
    for view_name, location, target, lens in views:
        render(camera, f"{label}-{view_name}.png", location, target, lens)
    report["variants"][label] = {"material": material, "settings": settings or "r210-control"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R219_SKIN_OPTICS=" + json.dumps(report, sort_keys=True))
