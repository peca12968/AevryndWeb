import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cornea-response-r175.blend"
CANDIDATE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-clearance-matched-lids-r181.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-clearance-matched-lids-r181.collision-audit.json"
BODY = "AevryndFemaleBodyBaseV118"


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def face_self_intersections(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    bvh = BVHTree.FromPolygons(points, faces, all_triangles=False)
    vertex_sets = [set(face) for face in faces]
    centers = [sum((points[index] for index in face), points[face[0]] * 0.0) / len(face) for face in faces]
    pairs = set()
    for first, second in bvh.overlap(bvh):
        if first == second:
            continue
        pair = tuple(sorted((first, second)))
        if pair in pairs or vertex_sets[first] & vertex_sets[second]:
            continue
        if not any(abs(point.x) < 0.12 and point.y < 0.045 and 1.40 < point.z < 1.64 for point in (centers[first], centers[second])):
            continue
        pairs.add(pair)
    return len(pairs)


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    eye_names = sorted(obj.name for obj in bpy.data.objects if obj.type == "MESH" and obj.name.startswith(("Eye_L_", "Eye_R_")))
    frames = {}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body = bpy.data.objects[BODY]
        body_tree = tree(body, depsgraph)
        values = {name: len(body_tree.overlap(tree(bpy.data.objects[name], depsgraph))) for name in eye_names}
        values["bodyFaceSelfIntersections"] = face_self_intersections(body, depsgraph)
        frames[str(frame)] = values
    nonfinite = sum(not all(math.isfinite(value) for value in point.co) for key in bpy.data.objects[BODY].data.shape_keys.key_blocks for point in key.data)
    return {"frames": frames, "nonfiniteShapeKeyPoints": nonfinite}


baseline = snapshot(BASELINE)
candidate = snapshot(CANDIDATE)
regressions = []
for frame, values in candidate["frames"].items():
    for layer, count in values.items():
        previous = baseline["frames"][frame][layer]
        if count > previous:
            regressions.append({"frame": frame, "layer": layer, "baseline": previous, "candidate": count})
if candidate["nonfiniteShapeKeyPoints"]:
    regressions.append({"contract": "nonfinite shape-key coordinates", "count": candidate["nonfiniteShapeKeyPoints"]})
report = {"baseline": str(BASELINE), "candidate": str(CANDIDATE), "baselineResults": baseline, "candidateResults": candidate, "regressions": regressions, "status": "PASS" if not regressions else "FAIL"}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R181_EYE_COLLISION=" + json.dumps({"status": report["status"], "regressions": regressions}, sort_keys=True))
if regressions:
    raise SystemExit(2)
