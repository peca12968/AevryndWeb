import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r9.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r12.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r12"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
HAIR = "AevryndFemaleGuideBob_v249r9"
REMOVED_CURVES = (13953, 13986, 13987, 13992)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
hair = bpy.data.objects[HAIR]
before_curves = len(hair.data.curves)
before_points = len(hair.data.points)
hair.data.remove_curves(indices=REMOVED_CURVES)
hair.name = "AevryndFemaleGuideBob_v249r12"
hair.data.name = "AevryndFemaleGuideBobData_v249r12"
hair["aevrynd_candidate"] = "v249-mainline-hair-r12"
hair["aevrynd_removed_collision_curves"] = json.dumps(REMOVED_CURVES)
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r12"
scene["aevrynd_release_state"] = "MAINLINE_GROOM_VISUAL_AND_COLLISION_AUDIT_REQUIRED"

camera = bpy.data.objects.get("Camera") or next(obj for obj in bpy.data.objects if obj.type == "CAMERA")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
views = (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
)
for name, location, target, lens in views:
    scene.frame_set(1)
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R12=" + json.dumps({
    "output": str(OUTPUT),
    "removed_curves": REMOVED_CURVES,
    "curves_before": before_curves,
    "curves_after": len(hair.data.curves),
    "points_before": before_points,
    "points_after": len(hair.data.points),
}, sort_keys=True))
