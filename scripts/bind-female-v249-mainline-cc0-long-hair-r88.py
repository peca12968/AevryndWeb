import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-long-hair-collision-r87.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-long-hair-bound-r88.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cc0-long-hair-bound-r88"
HAIR = (
    "AevryndFemaleCC0LongHairFitMain_v249r86",
    "AevryndFemaleCC0LongHairFitFlyaway_v249r86",
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, frame, location, target, lens):
    scene = bpy.context.scene
    scene.frame_set(frame)
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
rig = bpy.data.objects["AevryndFemaleRig"]
for name in HAIR:
    obj = bpy.data.objects[name]
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    obj["aevrynd_revision"] = "v249-mainline-cc0-long-hair-bound-r88"
    obj["aevrynd_primary_binding"] = "rigid head bone; strand secondary motion remains a runtime layer"

scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "cc0-long-hair-bound-r88"
scene["aevrynd_release_state"] = "R88_STATIC_DYNAMIC_AND_VISUAL_REVIEW_REQUIRED"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
for args in (
    ("01-frame1-front", 1, (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("02-frame1-three-quarter", 1, (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("03-frame20-front", 20, (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("04-frame20-three-quarter", 20, (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
):
    render(camera, *args)

report = {
    "source": str(SOURCE), "output": str(OUTPUT), "hair": list(HAIR),
    "binding": "head bone", "secondary_motion": "not yet integrated", "status": "AUDIT_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_CC0_LONG_HAIR_BOUND_R88=" + json.dumps(report, sort_keys=True))
