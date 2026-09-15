"""Render r1022 with brows and lashes visible under the fixed review rig."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-wetline-optics-r1022-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1022-integrated-eye-review.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1022-integrated-eye-review"


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene; scene.frame_set(1); bpy.context.view_layer.update()
hidden = []
for obj in scene.objects:
    is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
    is_brow_or_lash = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
    if is_hair and not is_brow_or_lash and not obj.hide_render:
        obj.hide_render = True; hidden.append(obj.name)

RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 1000
camera = scene.camera; camera.data.lens = 105; rendered = []
for view, location, target in (
    ("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)),
    ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
    ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
    ("profile-left", (0.43, -0.115, 1.490), (0.020, -0.055, 1.482)),
):
    camera.location = location; look_at(camera, target)
    path = RENDER_DIR / f"{view}.png"; scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True); rendered.append(str(path))

REPORT.write_text(json.dumps({"source": str(SOURCE), "rendered": rendered, "visible": "face, eyes, brows and lashes", "hidden": hidden, "lighting": "inherited fixed r1001 review rig", "status": "VISUAL_REVIEW_REQUIRED", "websitePromotionApproved": False}, indent=2), encoding="utf-8")
print("AEVRYND_R1022_INTEGRATED_EYE_REVIEW=" + json.dumps({"rendered": rendered, "status": "VISUAL_REVIEW_REQUIRED"}, sort_keys=True))
