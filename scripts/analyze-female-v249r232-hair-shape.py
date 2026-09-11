import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-smoothed-hair-r232.blend"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * fraction)))
    return ordered[index]


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
hair = bpy.data.objects[MAIN]
matrix = hair.matrix_world
lengths = []
terminal_steps = []
root_rows = []
tip_rows = []
front_crossing = 0
temple_crossing = 0

for curve_index, curve in enumerate(hair.data.curves):
    start = curve.first_point_index
    end = start + curve.points_length
    points = [matrix @ hair.data.points[index].position for index in range(start, end)]
    if len(points) < 2:
        continue
    length = sum((points[index] - points[index - 1]).length for index in range(1, len(points)))
    step = (points[-1] - points[-2]).length
    lengths.append(length)
    terminal_steps.append(step)
    root_rows.append((curve_index, *points[0]))
    tip_rows.append((curve_index, *points[-1]))
    if any(abs(point.x) < 0.13 and point.y < -0.055 and 1.38 < point.z < 1.75 for point in points):
        front_crossing += 1
    if any(0.10 < abs(point.x) < 0.28 and point.y < -0.035 and 1.38 < point.z < 1.72 for point in points):
        temple_crossing += 1

radius = hair.data.attributes.get("radius")
radius_values = [float(item.value) for item in radius.data] if radius else []
fly = bpy.data.objects.get(FLY)
report = {
    "source": str(SOURCE),
    "main": {
        "curves": len(hair.data.curves),
        "points": len(hair.data.points),
        "lengthM": {
            "minimum": min(lengths),
            "p10": percentile(lengths, 0.10),
            "median": percentile(lengths, 0.50),
            "p90": percentile(lengths, 0.90),
            "maximum": max(lengths),
        },
        "terminalStepM": {
            "minimum": min(terminal_steps),
            "median": percentile(terminal_steps, 0.50),
            "p95": percentile(terminal_steps, 0.95),
            "maximum": max(terminal_steps),
        },
        "radiusUm": {
            "minimum": min(radius_values) * 1.0e6 if radius_values else None,
            "median": percentile(radius_values, 0.50) * 1.0e6 if radius_values else None,
            "maximum": max(radius_values) * 1.0e6 if radius_values else None,
        },
        "frontCrossingCurves": front_crossing,
        "templeCrossingCurves": temple_crossing,
        "rootBounds": {
            "minimum": [min(row[axis] for row in root_rows) for axis in range(1, 4)],
            "maximum": [max(row[axis] for row in root_rows) for axis in range(1, 4)],
        },
        "tipBounds": {
            "minimum": [min(row[axis] for row in tip_rows) for axis in range(1, 4)],
            "maximum": [max(row[axis] for row in tip_rows) for axis in range(1, 4)],
        },
    },
    "flyaway": {
        "present": fly is not None,
        "curves": len(fly.data.curves) if fly else 0,
        "points": len(fly.data.points) if fly else 0,
        "hideRender": fly.hide_render if fly else None,
        "hideViewport": fly.hide_viewport if fly else None,
    },
}
print("AEVRYND_V249R232_HAIR_SHAPE=" + json.dumps(report, sort_keys=True))
