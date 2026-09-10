import json
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get(
    "AEVRYND_11SHOT_SOURCE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend",
))
RENDER_DIR = Path(os.environ.get(
    "AEVRYND_11SHOT_OUT",
    ROOT.parent / "Temp/female-realism/review-11shot-v249",
))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, frame, location, target, lens, resolution):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd Review Camera"]
shots = (
    ("01-full-front", 1, (0.0, -4.0, 0.90), (0.0, 0.0, 0.86), 70, (900, 1200)),
    ("02-full-left-three-quarter", 1, (2.35, -3.30, 0.95), (0.0, 0.0, 0.86), 70, (900, 1200)),
    ("03-full-left-profile", 1, (4.0, -0.05, 0.92), (0.0, 0.0, 0.86), 70, (900, 1200)),
    ("04-full-back", 1, (0.0, 4.0, 0.90), (0.0, 0.0, 0.86), 70, (900, 1200)),
    ("05-full-right-profile", 1, (-4.0, -0.05, 0.92), (0.0, 0.0, 0.86), 70, (900, 1200)),
    ("06-pose-front", 20, (0.0, -3.7, 0.98), (0.0, 0.0, 0.90), 70, (900, 1200)),
    ("07-pose-three-quarter", 20, (2.20, -3.15, 1.00), (0.0, 0.0, 0.90), 70, (900, 1200)),
    ("08-face-front", 1, (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
    ("09-face-three-quarter", 1, (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88, (1000, 1000)),
    ("10-face-profile", 1, (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88, (1000, 1000)),
    ("11-hair-top", 1, (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78, (1000, 1000)),
)
for shot in shots:
    render(camera, *shot)
print("AEVRYND_11SHOT_V249=" + json.dumps({"shots": [shot[0] for shot in shots], "count": len(shots)}))



