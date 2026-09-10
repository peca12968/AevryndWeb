import array
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-anatomical-hairline-fade-r187.blend"
RUNTIME = ROOT / "assets-source/aevrynd-character/runtime-groom-v249r94"
OUT = ROOT.parent / "Temp/female-realism/v249r188-runtime-family-clumps-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-runtime-family-clumps-r188.sweep-report.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
SAMPLES = 20
VARIANTS = (
    ("a-control", 0.0),
    ("b-light", 0.18),
    ("c-balanced", 0.32),
    ("d-strong", 0.46),
)


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def sample_curve(points, t):
    position = t * (len(points) - 1)
    first = min(len(points) - 2, int(position))
    blend = position - first
    return points[first].lerp(points[first + 1], blend)


def curve_points(obj, curve):
    return [obj.data.points[curve.first_point_index + index].position.copy() for index in range(curve.points_length)]


def build_family_centers(obj, guide_map):
    totals = {}
    counts = {}
    for curve_index, curve in enumerate(obj.data.curves):
        family = guide_map[curve_index]
        points = curve_points(obj, curve)
        if family not in totals:
            totals[family] = [Vector((0.0, 0.0, 0.0)) for _ in range(SAMPLES)]
            counts[family] = 0
        for sample_index in range(SAMPLES):
            totals[family][sample_index] += sample_curve(points, sample_index / (SAMPLES - 1))
        counts[family] += 1
    return {
        family: [value / counts[family] for value in values]
        for family, values in totals.items()
    }, counts


def apply_clumping(obj, guide_map, centers, strength):
    obj.data = obj.data.copy()
    moved = 0
    root_maximum = 0.0
    maximum = 0.0
    total = 0.0
    for curve_index, curve in enumerate(obj.data.curves):
        family_center = centers[guide_map[curve_index]]
        for local_index in range(curve.points_length):
            point = obj.data.points[curve.first_point_index + local_index]
            t = local_index / max(1, curve.points_length - 1)
            rise = smoothstep(0.04, 0.34, t)
            tip_release = 1.0 - 0.38 * smoothstep(0.78, 1.0, t)
            weight = strength * rise * tip_release
            center = sample_curve(family_center, t)
            delta = (center - point.position) * weight
            point.position += delta
            distance = delta.length
            if local_index == 0:
                root_maximum = max(root_maximum, distance)
            if distance > 1e-8:
                moved += 1
                maximum = max(maximum, distance)
                total += distance
    obj.data.update_tag()
    return {
        "pointsMoved": moved,
        "maximumMoveMm": maximum * 1000.0,
        "meanMovedPointMm": (total / moved * 1000.0) if moved else 0.0,
        "maximumRootMoveMm": root_maximum * 1000.0,
    }


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


mapping = array.array("H")
mapping.frombytes((RUNTIME / "follow-guide.u16").read_bytes())
OUT.mkdir(parents=True, exist_ok=True)
report = {}
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    main = bpy.data.objects[MAIN]
    guide_map = mapping[:len(main.data.curves)]
    centers, family_counts = build_family_centers(main, guide_map)
    metrics = apply_clumping(main, guide_map, centers, strength) if strength else {
        "pointsMoved": 0, "maximumMoveMm": 0.0, "meanMovedPointMm": 0.0, "maximumRootMoveMm": 0.0,
    }
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-hair-back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.60), 88),
        ("04-hair-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    )
    for view_name, location, target, lens in views:
        render(camera, f"{label}-{view_name}.png", location, target, lens)
    report[label] = {
        "strength": strength,
        "families": len(centers),
        "minimumCurvesPerFamily": min(family_counts.values()),
        "maximumCurvesPerFamily": max(family_counts.values()),
        **metrics,
    }

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R188_FAMILY_CLUMPS=" + json.dumps(report, sort_keys=True))
