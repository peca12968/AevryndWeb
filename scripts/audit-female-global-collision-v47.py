import json
import sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


path = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
bpy.ops.wm.open_mainfile(filepath=str(path))
scene = bpy.context.scene


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


body = bpy.data.objects["AevryndFemaleBodyBase"]
garments = [bpy.data.objects[name] for name in ("Clothing_InnerTop", "Clothing_InnerShorts")]
hair = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.name.startswith("Hair")]
failures = []
frames = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(body, depsgraph)
    values = {}
    for obj in garments + hair:
        count = len(body_tree.overlap(tree(obj, depsgraph)))
        values["body__" + obj.name] = count
        if count:
            failures.append(f"frame {frame} body/{obj.name} {count}")
    undercut = tree(bpy.data.objects["HairUndercutScalp"], depsgraph)
    for obj in hair:
        if obj.name == "HairUndercutScalp":
            continue
        count = len(undercut.overlap(tree(obj, depsgraph)))
        values["undercut__" + obj.name] = count
        if count:
            failures.append(f"frame {frame} undercut/{obj.name} {count}")
    frames[str(frame)] = values
report = {"status": "PASS" if not failures else "FAIL", "frames": frames, "failures": failures}
print("AEVRYND_GLOBAL_COLLISION_V47=" + json.dumps(report))
if failures:
    raise SystemExit(1)
