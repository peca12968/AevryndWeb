"""Render the selected r1083 rest, measured peak and settle frames."""
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-layered-hair-motion-r1083-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1083-layered-hair-motion.render.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1083-layered-hair-motion-review"
FRAMES = (1, 21, 31, 61)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
OUT.mkdir(parents=True, exist_ok=True)
renders = []
for frame in FRAMES:
    scene.frame_set(frame)
    for view, location, target in (
        ("front", (0.0, -0.72, 1.445), (0.0, -0.025, 1.445)),
        ("three-quarter", (0.45, -0.62, 1.46), (0.0, -0.015, 1.445)),
        ("back", (0.0, 0.72, 1.445), (0.0, 0.025, 1.445)),
    ):
        scene.camera.location = location
        scene.camera.data.lens = 88
        look_at(scene.camera, target)
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.resolution_percentage = 100
        path = OUT / f"selected-f{frame:02d}-{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders.append({"frame": frame, "view": view, "path": str(path)})
REPORT.write_text(json.dumps({"revision": "v249r1083-motion-review", "source": str(SOURCE), "frames": list(FRAMES), "renders": renders}, indent=2), encoding="utf-8")
print("AEVRYND_R1083_MOTION_REVIEW=" + json.dumps({"renders": len(renders), "frames": list(FRAMES)}, sort_keys=True))
