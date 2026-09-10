import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-forehead-shadow-prune-r134-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def curves_in_band(obj, y_min, y_max):
    matrix = obj.matrix_world
    result = set()
    for curve_index, curve in enumerate(obj.data.curves):
        for point_index in range(curve.first_point_index, curve.first_point_index + curve.points_length):
            point = matrix @ obj.data.points[point_index].position
            if abs(point.x) <= 0.120 and y_min <= point.y <= y_max and 1.625 <= point.z <= 1.715:
                result.add(curve_index)
                break
    return result


def filtered_copy(source, name, excluded):
    retained = [
        (curve_index, curve)
        for curve_index, curve in enumerate(source.data.curves)
        if curve_index not in excluded
    ]
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves([curve.points_length for _, curve in retained])
    source_radius = source.data.attributes.get("radius")
    target_radius = data.attributes.get("radius") or data.attributes.new("radius", "FLOAT", "POINT")
    target_index = 0
    for _, curve in retained:
        for source_index in range(curve.first_point_index, curve.first_point_index + curve.points_length):
            data.points[target_index].position = source.data.points[source_index].position
            if source_radius:
                target_radius.data[target_index].value = source_radius.data[source_index].value
            target_index += 1
    for material in source.data.materials:
        data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = source.matrix_world
    obj["aevrynd_layer"] = "hair.study.forehead-shadow-prune"
    return obj, len(retained), target_index


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
main = bpy.data.objects[MAIN]
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)
report = {"source": str(SOURCE), "variants": []}

for suffix, location, target, lens in views:
    render(camera, f"a-baseline-{suffix}", location, target, lens)
report["variants"].append({"name": "a-baseline", "excludedCurves": 0})

main.hide_render = True
variants = (
    ("b-prune-deepest-23", curves_in_band(main, -0.150, -0.130)),
    ("c-prune-forehead-193", curves_in_band(main, -0.140, -0.120)),
)
for name, excluded in variants:
    filtered, curves, points = filtered_copy(main, "Aevrynd" + name.title().replace("-", "") + "_v249r134", excluded)
    for suffix, location, target, lens in views:
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({
        "name": name,
        "excludedCurves": len(excluded),
        "retainedCurves": curves,
        "retainedPoints": points,
    })
    filtered.hide_render = True

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R134_FOREHEAD_SHADOW_PRUNE=" + json.dumps(report, sort_keys=True))
