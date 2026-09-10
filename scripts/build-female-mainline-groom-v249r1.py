import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"
GROOM_SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authored-guide-bob-v378.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r1.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r1"
RENDER_DIR.mkdir(parents=True, exist_ok=True)

VISIBLE_GROOM = (
    "AevryndFemaleGuideBob_v378",
    "AevryndFemaleScalpCoverage_v378",
)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
rig = bpy.data.objects["AevryndFemaleRig"]

hidden_old = []
for obj in bpy.data.objects:
    layer = str(obj.get("aevrynd_layer", ""))
    if "hair" in obj.name.lower() or layer.startswith("hair"):
        obj.hide_render = True
        obj.hide_viewport = True
        hidden_old.append(obj.name)

with bpy.data.libraries.load(str(GROOM_SOURCE), link=False) as (source_data, target_data):
    target_data.objects = [name for name in VISIBLE_GROOM if name in source_data.objects]

appended = []
for obj in target_data.objects:
    if obj is None:
        continue
    if obj.name not in scene.collection.objects:
        scene.collection.objects.link(obj)
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.matrix_world = world
    obj.hide_render = False
    obj.hide_viewport = False
    obj["aevrynd_mainline_base"] = "aevrynd-female-authoring-v249.blend"
    obj["aevrynd_groom_geometry_source"] = "aevrynd-female-authored-guide-bob-v378.blend"
    obj["aevrynd_candidate"] = "v249-mainline-hair-r1"
    appended.append(obj.name)

if set(appended) != set(VISIBLE_GROOM):
    raise RuntimeError(f"Missing groom objects: expected {VISIBLE_GROOM}, loaded {appended}")

scene["aevrynd_mainline_base"] = "v249"
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r1"
scene["aevrynd_release_state"] = "MAINLINE_GROOM_VISUAL_AUDIT_REQUIRED"

camera = bpy.data.objects.get("Camera") or next(obj for obj in bpy.data.objects if obj.type == "CAMERA")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 900
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
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R1=" + json.dumps({
    "output": str(OUTPUT),
    "renders": str(RENDER_DIR),
    "hidden_old_hair": hidden_old,
    "visible_groom": appended,
}, sort_keys=True))
