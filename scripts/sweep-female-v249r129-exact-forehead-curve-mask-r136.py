import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-exact-forehead-curve-mask-r136-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def deepest_front_curves(obj):
    matrix = obj.matrix_world
    result = []
    for curve_index, curve in enumerate(obj.data.curves):
        for point_index in range(curve.first_point_index, curve.first_point_index + curve.points_length):
            point = matrix @ obj.data.points[point_index].position
            if abs(point.x) <= 0.120 and -0.150 <= point.y <= -0.130 and 1.625 <= point.z <= 1.715:
                result.append(curve_index)
                break
    return result


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
main = bpy.data.objects[MAIN]
radius = main.data.attributes["radius"]
original_radius = [item.value for item in radius.data]
targets = deepest_front_curves(main)
target_points = [
    point_index
    for curve_index in targets
    for point_index in range(
        main.data.curves[curve_index].first_point_index,
        main.data.curves[curve_index].first_point_index + main.data.curves[curve_index].points_length,
    )
]
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)

for suffix, location, target, lens in views:
    render(camera, f"a-baseline-{suffix}", location, target, lens)

for point_index in target_points:
    radius.data[point_index].value = 0.0
bpy.context.view_layer.update()
for suffix, location, target, lens in views:
    render(camera, f"b-original-object-mask-23-{suffix}", location, target, lens)

for point_index, value in enumerate(original_radius):
    radius.data[point_index].value = value
bpy.context.view_layer.update()
report = {
    "source": str(SOURCE),
    "method": "Set radius to zero on original object; preserve curve indices, material randomization and all other attributes",
    "targetCurves": targets,
    "targetCurveCount": len(targets),
    "targetPointCount": len(target_points),
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R136_EXACT_FOREHEAD_MASK=" + json.dumps(report, sort_keys=True))
