import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
OUT = ROOT.parent / "Temp/female-realism/blender-official-female-hair-styles-r143"
STYLES = (
    ("a-new-hair", 0.0, ("new hair",)),
    ("b-cyberpunk", 0.0, ("cyberpunk hair",)),
    ("c-long", 5.0, ("long hair main", "long hair strands")),
    ("d-curly", 10.0, ("curly hair",)),
    ("e-braids", 15.0, ("braided hair",)),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_area(name, energy, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
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
for obj in bpy.data.objects:
    if obj.type == "CURVES":
        obj.hide_render = True

camera_data = bpy.data.cameras.new("Aevrynd Official Hair Review Camera r143")
camera = bpy.data.objects.new("Aevrynd Official Hair Review Camera r143", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
key = make_area("Aevrynd Official Hair Key r143", 1150.0, 3.0, (1.0, 0.82, 0.70))
fill = make_area("Aevrynd Official Hair Fill r143", 820.0, 2.6, (0.55, 0.72, 1.0))
rim = make_area("Aevrynd Official Hair Rim r143", 980.0, 2.2, (0.82, 0.90, 1.0))
report = {"source": str(SOURCE), "license": "CC0", "styles": []}

for style_name, center_x, visible_names in STYLES:
    for obj in bpy.data.objects:
        if obj.type == "CURVES":
            obj.hide_render = obj.name not in visible_names
    center = Vector((center_x, 0.0, 14.88))
    key.location = (center_x - 2.9, -5.2, 17.5)
    fill.location = (center_x + 3.2, -3.8, 15.8)
    rim.location = (center_x, 3.6, 17.2)
    for light in (key, fill, rim):
        look_at(light, center)
    views = (
        ("front", (center_x, -7.0, 14.90), (center_x, 0.0, 14.90), 82),
        ("three-quarter", (center_x + 3.9, -5.4, 14.95), (center_x, 0.0, 14.88), 82),
        ("top", (center_x, -1.2, 20.5), (center_x, 0.0, 15.15), 78),
    )
    for suffix, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(OUT / f"{style_name}-{suffix}.png")
        bpy.ops.render.render(write_still=True)
    counts = {}
    for name in visible_names:
        obj = bpy.data.objects[name]
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        counts[name] = {
            "rawCurves": len(obj.data.curves),
            "evaluatedCurves": len(evaluated.data.curves),
        }
    report["styles"].append({"name": style_name, "objects": list(visible_names), "counts": counts})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_OFFICIAL_FEMALE_HAIR_STYLES_R143=" + json.dumps(report, sort_keys=True))
