import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-mouth-r200.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eye-aperture-r201.inspect.json"
BODY = "AevryndFemaleBodyBaseV118"


def world_bounds(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    if not points:
        return None
    return {
        "min": [min(point[i] for point in points) for i in range(3)],
        "max": [max(point[i] for point in points) for i in range(3)],
        "center": [(min(point[i] for point in points) + max(point[i] for point in points)) * 0.5 for i in range(3)],
    }


def evaluated_bounds(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        return {
            "vertices": len(points),
            "min": [min(point[i] for point in points) for i in range(3)],
            "max": [max(point[i] for point in points) for i in range(3)],
        }
    finally:
        evaluated.to_mesh_clear()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
report = {"source": str(SOURCE), "frames": {}, "objects": {}}

for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    if obj.type == "MESH" and (obj.name.startswith("Eye_L_") or obj.name.startswith("Eye_R_")):
        report["objects"][obj.name] = {
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "bounds": world_bounds(obj),
            "layer": obj.get("aevrynd_layer"),
            "role": obj.get("aevrynd_role"),
        }

for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    report["frames"][str(frame)] = {
        BODY: evaluated_bounds(bpy.data.objects[BODY], depsgraph),
        **{
            name: evaluated_bounds(bpy.data.objects[name], depsgraph)
            for name in report["objects"]
        },
    }

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R201_EYE_APERTURE=" + json.dumps({
    "objectCount": len(report["objects"]),
    "objects": list(report["objects"]),
    "report": str(REPORT),
}, sort_keys=True))
