import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r228-hair-density-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-hair-density-r228.sweep-report.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLYAWAY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"
VARIANTS = (
    ("a-control", 1.00, 1.00),
    ("b-75pct", 0.75, 1.10),
    ("c-55pct", 0.55, 1.22),
    ("d-40pct", 0.40, 1.38),
)


def stable_fraction(index, root):
    value = math.sin(index * 12.9898 + root.x * 78.233 + root.y * 37.719 + root.z * 19.913) * 43758.5453
    return value - math.floor(value)


def thin_curves(obj, keep_fraction, radius_scale):
    data = obj.data
    before_curves = len(data.curves)
    before_points = len(data.points)
    remove = []
    for curve in data.curves:
        root = data.points[curve.first_point_index].position
        if stable_fraction(curve.index, root) > keep_fraction:
            remove.append(curve.index)
    if remove:
        data.remove_curves(indices=remove)
    radius = data.attributes.get("radius")
    if radius:
        for item in radius.data:
            item.value *= radius_scale
    return {
        "keepFractionTarget": keep_fraction,
        "radiusScale": radius_scale,
        "curvesBefore": before_curves,
        "pointsBefore": before_points,
        "curvesRemoved": len(remove),
        "curvesAfter": len(data.curves),
        "pointsAfter": len(data.points),
        "actualKeepFraction": len(data.curves) / before_curves,
        "radiusMinimum": min(item.value for item in radius.data) if radius else None,
        "radiusMaximum": max(item.value for item in radius.data) if radius else None,
        "radiusMean": sum(item.value for item in radius.data) / len(radius.data) if radius else None,
    }


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": {}, "status": "VISUAL_SELECTION_PENDING"}
for label, keep_fraction, radius_scale in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    main = bpy.data.objects[MAIN]
    bpy.data.objects[FLYAWAY].hide_render = True
    metrics = thin_curves(main, keep_fraction, radius_scale) if keep_fraction < 1.0 else {
        "keepFractionTarget": 1.0,
        "radiusScale": 1.0,
        "curvesBefore": len(main.data.curves),
        "pointsBefore": len(main.data.points),
        "curvesRemoved": 0,
        "curvesAfter": len(main.data.curves),
        "pointsAfter": len(main.data.points),
        "actualKeepFraction": 1.0,
    }
    camera = bpy.data.objects["Aevrynd Review Camera"]
    render(camera, f"{label}-01-front.png", (0.0, -2.42, 1.48), (0.0, 0.0, 1.42), 88)
    render(camera, f"{label}-02-three-quarter.png", (1.75, -2.10, 1.52), (0.0, 0.0, 1.42), 88)
    render(camera, f"{label}-03-rear.png", (0.0, 2.42, 1.48), (0.0, 0.0, 1.42), 88)
    render(camera, f"{label}-04-hair-close.png", (0.0, -1.15, 1.57), (0.0, 0.0, 1.55), 92)
    report["variants"][label] = metrics
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R228_HAIR_DENSITY=" + json.dumps(report, sort_keys=True))
