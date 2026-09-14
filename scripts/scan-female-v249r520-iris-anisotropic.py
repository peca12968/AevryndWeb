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
original = []
for obj in irises:
    restored = obj.scale.copy()
    restored /= 0.60
    original.append(restored)
results = {}
for fx in (0.75, 0.85, 0.95, 1.00):
    for fy in (0.50, 0.55, 0.60, 0.65):
        for obj, source in zip(irises, original):
            obj.scale.x = source.x * fx
            obj.scale.y = source.y * fy
            obj.scale.z = source.z * 0.60
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(bpy.data.objects[BODY], dg)
        results[f"x{fx:.2f}-y{fy:.2f}"] = {obj.name: len(body_tree.overlap(tree(obj, dg))) for obj in irises}
print("AEVRYND_R520_IRIS_ANISOTROPIC_SCAN=" + json.dumps(results, sort_keys=True))
