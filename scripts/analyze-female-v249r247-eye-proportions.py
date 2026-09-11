import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-baked-seam-clearance-r247.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-r247-eye-proportions.json"
BODY = "AevryndFemaleBodyBaseV118"
EYE_CENTERS = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}


def world_mesh_points(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    return points


def bounds(points):
    return {
        axis: {
            "min": min(point[index] for point in points),
            "max": max(point[index] for point in points),
            "spanMm": 1000.0 * (max(point[index] for point in points) - min(point[index] for point in points)),
        }
        for index, axis in enumerate("xyz")
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
body_points = world_mesh_points(bpy.data.objects[BODY], depsgraph)
report = {"source": str(SOURCE), "eyes": {}}
for side, center_tuple in EYE_CENTERS.items():
    center = Vector(center_tuple)
    values = {}
    for part in ("Sclera", "Cornea", "Iris", "Pupil", "Catchlight"):
        obj = bpy.data.objects.get(f"Eye_{side}_{part}")
        if obj is None:
            continue
        values[part] = bounds(world_mesh_points(obj, depsgraph))
    neighborhood = [
        point for point in body_points
        if abs(point.x - center.x) <= 0.022 and abs(point.z - center.z) <= 0.014 and point.y < -0.085
    ]
    values["bodyNeighborhood"] = {"vertices": len(neighborhood), "bounds": bounds(neighborhood)}
    report["eyes"][side] = values

OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R247_EYE_PROPORTIONS=" + json.dumps(report, sort_keys=True))
