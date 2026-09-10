import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-hair-layer-isolation-r137"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
VARIANTS = (
    ("a-baseline", True, True, True),
    ("b-main-only", True, False, False),
    ("c-scalp-only", False, False, True),
    ("d-flyaway-only", False, True, False),
    ("e-main-and-scalp", True, False, True),
    ("f-no-hair-layers", False, False, False),
)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
objects = {
    "main": bpy.data.objects[MAIN],
    "flyaway": bpy.data.objects[FLY],
    "scalp": bpy.data.objects[SCALP],
}
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)
report = {"source": str(SOURCE), "variants": []}

for name, main_visible, fly_visible, scalp_visible in VARIANTS:
    objects["main"].hide_render = not main_visible
    objects["flyaway"].hide_render = not fly_visible
    objects["scalp"].hide_render = not scalp_visible
    for suffix, location, target, lens in views:
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({
        "name": name,
        "main": main_visible,
        "flyaway": fly_visible,
        "scalp": scalp_visible,
    })

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R137_HAIR_LAYER_ISOLATION=" + json.dumps(report, sort_keys=True))
