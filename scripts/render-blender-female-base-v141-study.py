import json
from pathlib import Path

import bpy
from mathutils import Vector


SOURCE = Path(r"D:\Download\Aevrynd\Temp\female-realism\blender-human-base-meshes-v1.4.1\extracted\human-base-meshes-bundle-v1.4.1\human_base_meshes_bundle.blend")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "Temp/female-realism/blender-human-base-meshes-v141-study"
REPORT = ROOT / "assets-source/aevrynd-character/blender-human-base-meshes-v141.study-report.json"
BODY = "GEO-body_female_realistic"
EYES = ("GEO-body_female_realistic.eye.L", "GEO-body_female_realistic.eye.R")
CENTER_X = -1.3400525


def material(name, color, roughness=0.48):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.32
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_area(name, location, energy, size, color, target):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)


def render(camera, name, location, target, lens, size):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
for obj in scene.objects:
    obj.hide_render = True
for name in (BODY, *EYES):
    bpy.data.objects[name].hide_render = False

skin = material("Aevrynd_CC0_Base_Study_Skin", (0.22, 0.075, 0.045, 1.0), 0.52)
eye = material("Aevrynd_CC0_Base_Study_Eye", (0.72, 0.75, 0.70, 1.0), 0.24)
assign(bpy.data.objects[BODY], skin)
for name in EYES:
    assign(bpy.data.objects[name], eye)

world = bpy.data.worlds.new("Aevrynd_CC0_Base_Study_World") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.016, 0.022, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.20
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False

camera_data = bpy.data.cameras.new("Aevrynd CC0 Study Camera")
camera = bpy.data.objects.new("Aevrynd CC0 Study Camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
add_area("Aevrynd Key", (CENTER_X - 0.65, -1.0, 1.9), 85, 0.65, (1.0, 0.70, 0.58), (CENTER_X, 0.0, 1.45))
add_area("Aevrynd Fill", (CENTER_X + 0.75, -0.55, 1.65), 45, 0.70, (0.58, 0.72, 1.0), (CENTER_X, 0.0, 1.45))
add_area("Aevrynd Rim", (CENTER_X, 0.75, 1.85), 100, 0.55, (1.0, 0.82, 0.68), (CENTER_X, 0.0, 1.50))
OUT.mkdir(parents=True, exist_ok=True)
views = (
    ("01-full-front", (CENTER_X, -4.25, 1.05), (CENTER_X, 0.0, 0.95), 76, (900, 1200)),
    ("02-face-front", (CENTER_X, -1.05, 1.63), (CENTER_X, 0.0, 1.60), 88, (1000, 1000)),
    ("03-face-three-quarter", (CENTER_X + 0.58, -0.88, 1.64), (CENTER_X, 0.0, 1.59), 88, (1000, 1000)),
    ("04-face-profile", (CENTER_X + 1.05, -0.02, 1.62), (CENTER_X, 0.0, 1.58), 92, (1000, 1000)),
    ("05-back", (CENTER_X, 4.25, 1.05), (CENTER_X, 0.0, 0.95), 76, (900, 1200)),
)
for values in views:
    render(camera, *values)

body = bpy.data.objects[BODY]
report = {
    "source": str(SOURCE),
    "license": "CC0",
    "officialSource": "https://www.blender.org/download/demo-files/",
    "bundleVersion": "1.4.1",
    "sourceSha256": "811F43ACCBB31A88266D932F8F5563B2D13586FCA0BA2693AAD1F5FE582B3515",
    "body": {"name": BODY, "vertices": len(body.data.vertices), "polygons": len(body.data.polygons)},
    "views": [values[0] for values in views],
    "status": "STRICT_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_BLENDER_FEMALE_BASE_V141_STUDY=" + json.dumps(report, sort_keys=True))
