import json
import statistics
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
PRE_COLLISION = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-long-hair-study-r85.blend"
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-precollision-geometry-blend-r142-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
VARIANTS = (
    ("a-r129-collision", 0.0),
    ("b-25pct-r85", 0.25),
    ("c-50pct-r85", 0.50),
    ("d-75pct-r85", 0.75),
    ("e-r85-precollision", 1.0),
)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(PRE_COLLISION))
pre_obj = bpy.data.objects[MAIN]
pre_matrix = pre_obj.matrix_world
pre_world = [pre_matrix @ point.position for point in pre_obj.data.points]
pre_lengths = [curve.points_length for curve in pre_obj.data.curves]

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
main = bpy.data.objects[MAIN]
if len(main.data.points) != len(pre_world):
    raise RuntimeError("r85/r129 main point count mismatch")
if [curve.points_length for curve in main.data.curves] != pre_lengths:
    raise RuntimeError("r85/r129 curve topology mismatch")
current_matrix = main.matrix_world
inverse = current_matrix.inverted()
current_world = [current_matrix @ point.position for point in main.data.points]
displacements = [(pre - current).length for pre, current in zip(pre_world, current_world)]
sorted_displacements = sorted(displacements)
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ("back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
)
report = {
    "source": str(SOURCE),
    "preCollision": str(PRE_COLLISION),
    "curveCount": len(main.data.curves),
    "pointCount": len(main.data.points),
    "displacementM": {
        "mean": statistics.fmean(displacements),
        "median": statistics.median(displacements),
        "p90": sorted_displacements[int(0.90 * (len(sorted_displacements) - 1))],
        "p99": sorted_displacements[int(0.99 * (len(sorted_displacements) - 1))],
        "maximum": max(displacements),
        "over0p5mm": sum(value > 0.0005 for value in displacements),
        "over2mm": sum(value > 0.002 for value in displacements),
    },
    "variants": [],
}

for name, blend in VARIANTS:
    for point_index, (current, pre) in enumerate(zip(current_world, pre_world)):
        world = current.lerp(pre, blend)
        main.data.points[point_index].position = inverse @ world
    bpy.context.view_layer.update()
    for suffix, location, target, lens in views:
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({"name": name, "preCollisionBlend": blend})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R142_PRECOLLISION_BLEND=" + json.dumps(report, sort_keys=True))
