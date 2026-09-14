import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-orbital-volume-r524-rejected.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-orbital-volume-r524.eye-envelope-study.json"
BODY = "AevryndFemaleBodyBaseV118"
EYE_OBJECTS = tuple(
    f"Eye_{side}_{part}"
    for side in ("L", "R")
    for part in ("Caruncle", "Cornea", "Iris", "Pupil", "Sclera", "TearMeniscus", "UpperLashes")
)
TESTED = (-2.0, -1.2, -0.8, -0.4, 0.0, 0.4, 0.8, 1.2, 2.0)
FRAMES = (1, 20)


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
objects = {name: bpy.data.objects[name] for name in EYE_OBJECTS}
original = {name: [vertex.co.copy() for vertex in obj.data.vertices] for name, obj in objects.items()}
results = {}
for millimeters in TESTED:
    movement = Vector((0.0, millimeters / 1000.0, 0.0))
    for name, obj in objects.items():
        local = obj.matrix_world.inverted().to_3x3() @ movement
        for vertex, source in zip(obj.data.vertices, original[name]):
            vertex.co = source + local
        obj.data.update()
    frame_result = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(bpy.data.objects[BODY], depsgraph)
        frame_result[str(frame)] = {
            name: len(body_tree.overlap(tree(obj, depsgraph))) for name, obj in objects.items()
        }
    results[f"{millimeters:.1f}"] = frame_result

report = {"source": str(SOURCE), "movementAxis": "signed world +Y", "testedMillimeters": TESTED, "frames": FRAMES, "results": results}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R524_EYE_ENVELOPE=" + json.dumps(report, sort_keys=True))
