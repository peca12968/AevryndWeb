import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-natural-long-hair-r94.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cc0-natural-long-hair-r94-scalp-isolation"
COVERAGE = "AevryndFemaleScalpCoverage_v378"
PART = "AevryndFemaleScalpPart_v249r25"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
camera.location = (0.0, -0.72, 1.60)
camera.data.lens = 88
look_at(camera, (0.0, -0.025, 1.595))
states = (
    ("none", False, False),
    ("part-only", False, True),
    ("coverage-only", True, False),
)
for name, show_coverage, show_part in states:
    bpy.data.objects[COVERAGE].hide_render = not show_coverage
    bpy.data.objects[PART].hide_render = not show_part
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("AEVRYND_R94_SCALP_ISOLATION=" + json.dumps({"output": str(OUT), "states": [state[0] for state in states]}, sort_keys=True))
