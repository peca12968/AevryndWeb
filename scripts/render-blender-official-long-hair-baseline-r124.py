import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
OUT = ROOT.parent / "Temp/female-realism/blender-official-long-hair-baseline-r124"
HAIR_MAIN = "long hair main"
HAIR_STRANDS = "long hair strands"
CENTER = Vector((5.0, 0.0, 14.88))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_area(name, location, energy, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, CENTER)
    return obj


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.world.color = (0.008, 0.012, 0.018)

# Curves from the other three examples are outside the crop, but hiding them
# avoids evaluating unrelated Geometry Nodes during this reference render.
for obj in bpy.data.objects:
    if obj.type == "CURVES" and obj.name not in {HAIR_MAIN, HAIR_STRANDS}:
        obj.hide_render = True
for name in (HAIR_MAIN, HAIR_STRANDS):
    obj = bpy.data.objects[name]
    obj.hide_render = False
    obj.hide_viewport = False
    obj.hide_set(False)

camera_data = bpy.data.cameras.new("Aevrynd Official Hair Review Camera r124")
camera = bpy.data.objects.new("Aevrynd Official Hair Review Camera r124", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
make_area("Aevrynd Official Hair Key r124", (2.1, -5.2, 17.5), 1150.0, 3.0, (1.0, 0.82, 0.70))
make_area("Aevrynd Official Hair Fill r124", (8.2, -3.8, 15.8), 820.0, 2.6, (0.55, 0.72, 1.0))
make_area("Aevrynd Official Hair Rim r124", (5.0, 3.6, 17.2), 980.0, 2.2, (0.82, 0.90, 1.0))

views = (
    ("01-front", (5.0, -7.0, 14.90), (5.0, 0.0, 14.90), 82),
    ("02-three-quarter", (8.9, -5.4, 14.95), (5.0, 0.0, 14.88), 82),
    ("03-profile", (11.8, 0.0, 14.95), (5.0, 0.0, 14.88), 86),
    ("04-back", (5.0, 6.9, 14.90), (5.0, 0.0, 14.88), 82),
    ("05-top", (5.0, -1.2, 20.5), (5.0, 0.0, 15.15), 78),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

main = bpy.data.objects[HAIR_MAIN]
strands = bpy.data.objects[HAIR_STRANDS]
report = {
    "source": str(SOURCE),
    "license": "CC0",
    "mainRawCurves": len(main.data.curves),
    "mainEvaluatedCurves": len(main.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.curves),
    "flyawayRawCurves": len(strands.data.curves),
    "views": [name for name, *_rest in views],
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_OFFICIAL_LONG_HAIR_BASELINE_R124=" + json.dumps(report, sort_keys=True))
