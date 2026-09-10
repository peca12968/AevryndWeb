from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"
OUT = ROOT.parent / "Temp/female-realism/scalp-response-sweep-v249"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens, resolution=1000):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUT / f"{name}.png")
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
material = bpy.data.materials["Aevrynd_Hair_Scalp"]
shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
camera = bpy.data.objects["Aevrynd Review Camera"]
for label, roughness, specular in (
    ("balanced", 0.66, 0.08),
    ("matte", 0.82, 0.04),
    ("deep-matte", 0.94, 0.018),
):
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = specular
    render(camera, f"{label}-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78)
    render(camera, f"{label}-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
    render(camera, f"{label}-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
    print("SCALP_RESPONSE", label, roughness, specular)
