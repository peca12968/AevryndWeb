import json
import math
import os
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ.get(
    "AEVRYND_FACE_BASELINE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r17.blend",
))
CANDIDATE = Path(os.environ.get(
    "AEVRYND_FACE_CANDIDATE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r18.blend",
))
OUTPUT = Path(os.environ.get(
    "AEVRYND_FACE_REPORT",
    ROOT / "assets-source/aevrynd-character/female-v249-mainline-face-r18.collision-audit.json",
))
BODY = "AevryndFemaleBodyBaseV118"


def evaluated_geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = evaluated_geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def regional_self_intersections(obj, depsgraph):
    points, faces = evaluated_geometry(obj, depsgraph)
    bvh = BVHTree.FromPolygons(points, faces, all_triangles=False)
    vertex_sets = [set(face) for face in faces]
    centers = [sum((points[i] for i in face), points[face[0]] * 0.0) / len(face) for face in faces]
    pairs = set()
    for first, second in bvh.overlap(bvh):
        if first == second or vertex_sets[first] & vertex_sets[second]:
            continue
        pair = tuple(sorted((first, second)))
        if pair in pairs:
            continue
        a, b = centers[first], centers[second]
        if any(abs(p.x) < 0.120 and p.y < 0.045 and 1.400 < p.z < 1.650 for p in (a, b)):
            pairs.add(pair)
    return len(pairs)


def collision_layers():
    names = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or obj.name == BODY:
            continue
        if obj.name.startswith(("Eye_", "Lip_", "Mouth_", "Clothing_")):
            names.append(obj.name)
    return sorted(names)


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    layers = collision_layers()
    frames = {}
    for frame in (1, 20):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body = bpy.data.objects[BODY]
        body_tree = tree(body, depsgraph)
        values = {
            name: len(body_tree.overlap(tree(bpy.data.objects[name], depsgraph)))
            for name in layers
        }
        values["body_face_self_intersections"] = regional_self_intersections(body, depsgraph)
        frames[str(frame)] = values
    return frames


baseline = snapshot(BASELINE)
candidate = snapshot(CANDIDATE)
regressions = []
for frame, values in candidate.items():
    for name, count in values.items():
        previous = baseline[frame].get(name)
        if previous is None or count > previous:
            regressions.append({
                "frame": int(frame),
                "layer": name,
                "baseline": previous,
                "candidate": count,
            })

bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
body = bpy.data.objects[BODY]
nonfinite = sum(
    not all(math.isfinite(value) for value in vertex.co)
    for vertex in body.data.vertices
)
if bpy.context.scene.get("aevrynd_mainline_baseline") != "v249":
    regressions.append({"contract": "candidate is not tagged as v249 mainline"})
if nonfinite:
    regressions.append({"contract": f"nonfinite vertices {nonfinite}"})

report = {
    "baseline": str(BASELINE),
    "candidate": str(CANDIDATE),
    "mainline_base": "v249",
    "frames": candidate,
    "nonfinite": nonfinite,
    "regressions": regressions,
    "status": "PASS" if not regressions else "FAIL",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_MAINLINE_FACE_AUDIT=" + json.dumps(report, sort_keys=True))
if regressions:
    raise SystemExit(2)
