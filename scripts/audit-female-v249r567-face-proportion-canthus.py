import hashlib
import json
import math
import struct
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
BASELINE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
CANDIDATE = ASSETS / "aevrynd-female-authoring-v249-mainline-face-proportion-canthus-r567.blend"
REPORT = ASSETS / "female-v249-mainline-face-proportion-canthus-r567.audit.json"
BODY = "AevryndFemaleBodyBaseV118"
OPTICAL = tuple(f"Eye_{side}_{part}" for side in ("L", "R") for part in ("Cornea", "Sclera"))
FACE_LAYERS = tuple(
    f"Eye_{side}_{part}"
    for side in ("L", "R")
    for part in ("Caruncle", "Cornea", "Iris", "Pupil", "Sclera", "TearMeniscus", "UpperLashes")
) + ("Mouth_OralCavity", "Mouth_Tongue", "Mouth_UpperTeeth")
FRAMES = (1, 20, 33, 61)


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def self_intersections(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    surface = BVHTree.FromPolygons(points, faces, all_triangles=False)
    sets = [set(face) for face in faces]
    return sum(1 for first, second in surface.overlap(surface) if first < second and not sets[first].intersection(sets[second]))


def digest(obj):
    value = hashlib.sha256()
    value.update(struct.pack("<II", len(obj.data.vertices), len(obj.data.polygons)))
    for vertex in obj.data.vertices:
        value.update(struct.pack("<fff", *vertex.co))
    for polygon in obj.data.polygons:
        value.update(struct.pack("<I", len(polygon.vertices)))
        for index in polygon.vertices:
            value.update(struct.pack("<I", index))
    return value.hexdigest()


def inventory(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    return {obj.name: digest(obj) for obj in bpy.data.objects if obj.type == "MESH"}


def shape_key_digest(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects[BODY]
    value = hashlib.sha256()
    for key in body.data.shape_keys.key_blocks:
        value.update(key.name.encode("utf-8"))
        for point in key.data:
            value.update(struct.pack("<fff", *point.co))
    return value.hexdigest()


def body_self_snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    result = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        result[str(frame)] = self_intersections(
            bpy.data.objects[BODY], bpy.context.evaluated_depsgraph_get()
        )
    return result


baseline_inventory = inventory(BASELINE)
candidate_inventory = inventory(CANDIDATE)
changed = sorted(name for name, value in baseline_inventory.items() if candidate_inventory.get(name) != value)
added = sorted(set(candidate_inventory) - set(baseline_inventory))
removed = sorted(set(baseline_inventory) - set(candidate_inventory))
failures = []
expected_changed = []
if changed != expected_changed:
    failures.append({"category": "unexpectedGeometryChanges", "expected": expected_changed, "actual": changed})
if added or removed:
    failures.append({"category": "inventoryChange", "added": added, "removed": removed})

baseline_shape_key_digest = shape_key_digest(BASELINE)
candidate_shape_key_digest = shape_key_digest(CANDIDATE)
if baseline_shape_key_digest == candidate_shape_key_digest:
    failures.append({"category": "bodyShapeKeysDidNotChange"})

baseline_self = body_self_snapshot(BASELINE)
bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
shape_keys = [key.name for key in body.data.shape_keys.key_blocks]
nonfinite = sum(not all(math.isfinite(value) for value in point.co) for key in body.data.shape_keys.key_blocks for point in key.data)
if nonfinite:
    failures.append({"category": "nonfiniteShapeKeyPoints", "count": nonfinite})

collision = {}
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(body, depsgraph)
    candidate_self = self_intersections(body, depsgraph)
    collision[str(frame)] = {
        "faceLayerOverlaps": {},
        "baselineBodySelfIntersections": baseline_self[str(frame)],
        "bodySelfIntersections": candidate_self,
    }
    if candidate_self > baseline_self[str(frame)]:
        failures.append({"category": "bodySelfIntersectionRegression", "frame": frame, "baseline": baseline_self[str(frame)], "candidate": candidate_self})
    for name in FACE_LAYERS:
        overlaps = len(body_tree.overlap(tree(bpy.data.objects[name], depsgraph)))
        collision[str(frame)]["faceLayerOverlaps"][name] = overlaps
        if overlaps:
            failures.append({"category": "faceLayerOverlap", "frame": frame, "layer": name, "count": overlaps})

report = {
    "baseline": str(BASELINE),
    "candidate": str(CANDIDATE),
    "changedMeshes": changed,
    "addedMeshes": added,
    "removedMeshes": removed,
    "shapeKeys": shape_keys,
    "baselineShapeKeyDigest": baseline_shape_key_digest,
    "candidateShapeKeyDigest": candidate_shape_key_digest,
    "nonfiniteShapeKeyPoints": nonfinite,
    "frames": list(FRAMES),
    "collision": collision,
    "failures": failures,
    "status": "PASS" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R567_AUDIT=" + json.dumps({"status": report["status"], "changedMeshes": changed, "failures": failures}, sort_keys=True))
if failures:
    raise SystemExit(2)
