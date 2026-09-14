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
irises = [bpy.data.objects[f"Eye_{side}_Iris"] for side in ("L", "R")]
for obj in irises:
    obj.location.y -= 0.0025
original_scale = [obj.scale.copy() for obj in irises]
results = {}
for factor in (0.90, 0.82, 0.75, 0.68, 0.60, 0.52, 0.45):
    for obj, source_scale in zip(irises, original_scale):
        obj.scale = source_scale * factor
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(bpy.data.objects[BODY], dg)
    results[str(factor)] = {obj.name: len(body_tree.overlap(tree(obj, dg))) for obj in irises}
print("AEVRYND_R520_IRIS_SCALE_SCAN=" + json.dumps(results, sort_keys=True))
