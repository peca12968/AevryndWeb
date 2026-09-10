import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r38.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eye-stack.json"
BODY = "AevryndFemaleBodyBaseV118"
EYE_CENTERS = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}


def world_points(obj):
    return [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]


def bounds(points):
    return {
        axis: {
            "min": min(point[index] for point in points),
            "max": max(point[index] for point in points),
            "span_mm": 1000.0 * (
                max(point[index] for point in points) - min(point[index] for point in points)
            ),
        }
        for index, axis in enumerate("xyz")
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
body_points = world_points(body)
report = {"source": str(SOURCE), "eyes": {}}

for side, center_tuple in EYE_CENTERS.items():
    center = Vector(center_tuple)
    eye = {"declared_center": list(center)}
    for part in ("Sclera", "Cornea", "Iris", "LimbalRing", "Pupil", "Catchlight"):
        obj = bpy.data.objects.get(f"Eye_{side}_{part}")
        if obj is None or obj.type != "MESH":
            continue
        points = world_points(obj)
        centroid = sum(points, Vector()) / len(points)
        eye[part] = {
            "vertices": len(points),
            "centroid": list(centroid),
            "bounds": bounds(points),
        }

    # Sample the visible facial surface surrounding the intended aperture.  The
    # model looks toward -Y, so the most negative Y value is the front surface.
    neighborhood = [
        point for point in body_points
        if abs(point.x - center.x) <= 0.021 and abs(point.z - center.z) <= 0.011
    ]
    eye["body_neighborhood"] = {
        "vertices": len(neighborhood),
        "bounds": bounds(neighborhood),
        "front_y": min(point.y for point in neighborhood),
        "back_y": max(point.y for point in neighborhood),
    }
    report["eyes"][side] = eye

OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_EYE_STACK=" + json.dumps(report, sort_keys=True))
