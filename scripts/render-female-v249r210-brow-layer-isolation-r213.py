import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r213-brow-layer-isolation"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-brow-layer-isolation-r213.review.json"
FIBERS = ("Brow_L", "Brow_R")
DENSITY = ("Brow_L_Density", "Brow_R_Density")
STATES = (
    ("a-composite", True, True),
    ("b-fibers-only", True, False),
    ("c-density-only", False, True),
)


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
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
report = {"source": str(SOURCE), "states": {}}
for label, show_fibers, show_density in STATES:
    for name in FIBERS:
        bpy.data.objects[name].hide_render = not show_fibers
    for name in DENSITY:
        bpy.data.objects[name].hide_render = not show_density
    render(camera, f"{label}-01-close.png", (0.0, -0.445, 1.638), (0.0, -0.076, 1.638), 132, (1280, 760))
    render(camera, f"{label}-02-face.png", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000))
    report["states"][label] = {"fibers": show_fibers, "density": show_density}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R213_BROW_ISOLATION=" + json.dumps(report, sort_keys=True))
