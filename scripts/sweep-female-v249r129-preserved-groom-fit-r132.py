import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-preserved-groom-fit-r132-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
VARIANTS = (
    ("a-zero", (0.0, 0.0, 0.0)),
    ("b-forward-1p5-down-3", (0.0, -0.0015, -0.0030)),
    ("c-forward-3-down-6", (0.0, -0.0030, -0.0060)),
    ("d-forward-4p5-down-9", (0.0, -0.0045, -0.0090)),
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
objects = (bpy.data.objects[MAIN], bpy.data.objects[FLY])
original = {obj.name: obj.matrix_world.copy() for obj in objects}
bpy.data.objects[SCALP].hide_render = True
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)
report = {"source": str(SOURCE), "scalpHidden": True, "geometryChanged": False, "variants": []}

for name, delta_values in VARIANTS:
    delta = Vector(delta_values)
    for obj in objects:
        matrix = original[obj.name].copy()
        matrix.translation += delta
        obj.matrix_world = matrix
    for suffix, location, target, lens in views:
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({"name": name, "translationM": list(delta)})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R132_PRESERVED_GROOM_FIT=" + json.dumps(report, sort_keys=True))
