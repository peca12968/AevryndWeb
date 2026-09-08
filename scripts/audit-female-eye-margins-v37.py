import hashlib
import json
import math
import struct
import sys

import bpy
from mathutils.bvhtree import BVHTree


def inputs():
    values = sys.argv[sys.argv.index("--") + 1:]
    if len(values) != 2:
        raise SystemExit("expected baseline.blend candidate.blend")
    return values


def signature(obj):
    digest = hashlib.sha256()
    digest.update(struct.pack("<II", len(obj.data.vertices), len(obj.data.polygons)))
    for vertex in obj.data.vertices:
        digest.update(struct.pack("<fff", *vertex.co))
    for polygon in obj.data.polygons:
        digest.update(struct.pack("<I", len(polygon.vertices)))
        for index in polygon.vertices:
            digest.update(struct.pack("<I", index))
    return digest.hexdigest()


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    return {obj.name: signature(obj) for obj in bpy.data.objects if obj.type == "MESH"}


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


baseline_path, candidate_path = inputs()
baseline = snapshot(baseline_path)
candidate = snapshot(candidate_path)
failures = []
expected_names = set(baseline) | {"Eye_L_Caruncle", "Eye_R_Caruncle"}
if set(candidate) != expected_names:
    failures.append("candidate object set is not baseline plus two caruncles")
allowed_changes = {"Eye_L_TearMeniscus", "Eye_R_TearMeniscus"}
unexpected_changes = [
    name for name, value in baseline.items()
    if name not in allowed_changes and candidate.get(name) != value
]
if unexpected_changes:
    failures.append(f"unexpected geometry changes: {unexpected_changes}")

bpy.ops.wm.open_mainfile(filepath=candidate_path)
scene = bpy.context.scene
if scene.get("aevrynd_eye_revision") != 37:
    failures.append("scene eye revision is not 37")
for side in ("L", "R"):
    meniscus = bpy.data.objects[f"Eye_{side}_TearMeniscus"]
    caruncle = bpy.data.objects[f"Eye_{side}_Caruncle"]
    if len(meniscus.data.vertices) != 94 or len(meniscus.data.polygons) != 46:
        failures.append(f"Eye_{side}_TearMeniscus topology is invalid")
    if len(caruncle.data.vertices) != 15 or len(caruncle.data.polygons) != 14:
        failures.append(f"Eye_{side}_Caruncle topology is invalid")
    for obj in (meniscus, caruncle):
        if obj.parent_type != "BONE" or obj.parent_bone != "head":
            failures.append(f"{obj.name} is not bound to the head bone")

frames = {}
body = bpy.data.objects["AevryndFemaleBodyBase"]
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_bvh = world_tree(body, depsgraph)
    frame_report = {}
    for side in ("L", "R"):
        names = {
            "meniscus": f"Eye_{side}_TearMeniscus",
            "caruncle": f"Eye_{side}_Caruncle",
            "sclera": f"Eye_{side}_Sclera",
            "cornea": f"Eye_{side}_Cornea",
        }
        trees = {key: world_tree(bpy.data.objects[name], depsgraph) for key, name in names.items()}
        values = {
            "meniscus_body": len(trees["meniscus"].overlap(body_bvh)),
            "caruncle_body": len(trees["caruncle"].overlap(body_bvh)),
            "caruncle_sclera": len(trees["caruncle"].overlap(trees["sclera"])),
            "caruncle_cornea": len(trees["caruncle"].overlap(trees["cornea"])),
            "caruncle_meniscus": len(trees["caruncle"].overlap(trees["meniscus"])),
            "meniscus_cornea": len(trees["meniscus"].overlap(trees["cornea"])),
        }
        frame_report[side] = values
        for label, count in values.items():
            if count:
                failures.append(f"frame {frame} eye {side} {label} has {count} triangle overlaps")
    frames[str(frame)] = frame_report

non_finite = sum(
    not all(math.isfinite(value) for value in vertex.co)
    for obj in bpy.data.objects if obj.type == "MESH" for vertex in obj.data.vertices
)
if non_finite:
    failures.append(f"candidate contains {non_finite} non-finite vertices")
report = {
    "unchanged_baseline_mesh_objects": sum(
        candidate.get(name) == value for name, value in baseline.items() if name not in allowed_changes
    ),
    "rebuilt_meniscus_layers": 2,
    "new_caruncle_layers": 2,
    "frames": frames,
    "non_finite_vertices": non_finite,
}
print("AEVRYND_EYE_MARGINS_V37_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
