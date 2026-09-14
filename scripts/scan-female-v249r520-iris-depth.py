import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-eye-ratio-r520.blend"
BODY = "AevryndFemaleBodyBaseV118"


def tree(obj, dg):
    evaluated = obj.evaluated_get(dg)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
scene.frame_set(1)
scene.view_layers.update()
irises = [bpy.data.objects[f"Eye_{side}_Iris"] for side in ("L", "R")]
original = [obj.location.y for obj in irises]
results = {}
for relative_mm in (8, 10, 12, 14, 16, 18, 20):
    for obj, source_y in zip(irises, original):
        obj.location.y = source_y + relative_mm / 1000.0
    scene.view_layers.update()
    dg = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(bpy.data.objects[BODY], dg)
    results[str(relative_mm)] = {obj.name: len(body_tree.overlap(tree(obj, dg))) for obj in irises}
print("AEVRYND_R520_IRIS_DEPTH_SCAN=" + json.dumps(results, sort_keys=True))
