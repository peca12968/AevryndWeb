import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eye-aperture-r83.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-cleanup-r84.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-hair-cleanup-r84"
KEEP_VISIBLE = {
    "AevryndFemaleGuideBob_v249r25",
    "AevryndFemaleNapeFiberFill_v249r17",
    "AevryndFemaleScalpCoverage_v378",
    "AevryndFemaleScalpPart_v249r25",
}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def render(camera, name, location, target, lens, resolution=(1000, 1000)):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = resolution
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
hidden = []
visible = []
for obj in bpy.data.objects:
    if not is_hair(obj):
        continue
    keep = obj.name in KEEP_VISIBLE
    obj.hide_render = not keep
    obj.hide_viewport = not keep
    obj["aevrynd_hair_visibility_revision"] = "v249-mainline-hair-cleanup-r84"
    (visible if keep else hidden).append(obj.name)
if set(visible) != KEEP_VISIBLE:
    raise RuntimeError(f"Missing intended v249 hair layers: {sorted(KEEP_VISIBLE - set(visible))}")
scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "hair-cleanup-r84"
scene["aevrynd_release_state"] = "R84_STRICT_VISUAL_COLLISION_AND_RUNTIME_REVIEW_REQUIRED"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
    ("06-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
)
for name, location, target, lens in views:
    render(camera, name, location, target, lens)
report = {
    "source": str(SOURCE), "output": str(OUTPUT),
    "visible_hair_objects": sorted(visible),
    "hidden_legacy_hair_objects": sorted(hidden),
    "geometry_changed": False,
    "root_cause": "face review scripts restored every historical hair object to visible",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_HAIR_CLEANUP_R84=" + json.dumps(report, sort_keys=True))
