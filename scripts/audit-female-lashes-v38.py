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
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


baseline_path, candidate_path = inputs()
baseline = snapshot(baseline_path)
candidate = snapshot(candidate_path)
failures = []
lash_names = {
    f"Eye_{side}_{kind}Lashes"
    for side in ("L", "R") for kind in ("Upper", "Lower")
}
if set(baseline) != set(candidate):
    failures.append("mesh object set changed")
unexpected = [name for name, value in baseline.items() if name not in lash_names and candidate.get(name) != value]
if unexpected:
    failures.append(f"unexpected geometry changes: {unexpected}")

bpy.ops.wm.open_mainfile(filepath=candidate_path)
scene = bpy.context.scene
if scene.get("aevrynd_eye_revision") != 38:
    failures.append("scene eye revision is not 38")
topology = {}
for side in ("L", "R"):
    for kind, fibers, vertices, faces in (("Upper", 26, 390, 312), ("Lower", 12, 180, 144)):
        obj = bpy.data.objects[f"Eye_{side}_{kind}Lashes"]
        topology[obj.name] = {
            "fibers": int(obj["aevrynd_fiber_count"]),
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons),
            "length_range_m": [float(obj["aevrynd_length_min_m"]), float(obj["aevrynd_length_max_m"])],
        }
        if topology[obj.name]["fibers"] != fibers or len(obj.data.vertices) != vertices or len(obj.data.polygons) != faces:
            failures.append(f"{obj.name} topology is invalid")
        minimum, maximum = topology[obj.name]["length_range_m"]
        if kind == "Upper" and not (0.0022 <= minimum <= 0.0035 and 0.0070 <= maximum <= 0.0086):
            failures.append(f"{obj.name} length range is invalid")
        if kind == "Lower" and not (0.0014 <= minimum <= 0.0020 and 0.0040 <= maximum <= 0.0046):
            failures.append(f"{obj.name} length range is invalid")
        if obj.parent_type != "BONE" or obj.parent_bone != "head":
            failures.append(f"{obj.name} is not bound to the head bone")

body = bpy.data.objects["AevryndFemaleBodyBase"]
frames = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_bvh = world_tree(body, depsgraph)
    frame_report = {}
    for side in ("L", "R"):
        upper = world_tree(bpy.data.objects[f"Eye_{side}_UpperLashes"], depsgraph)
        lower = world_tree(bpy.data.objects[f"Eye_{side}_LowerLashes"], depsgraph)
        sclera = world_tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph)
        cornea = world_tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph)
        values = {
            "upper_body": len(upper.overlap(body_bvh)),
            "lower_body": len(lower.overlap(body_bvh)),
            "upper_sclera": len(upper.overlap(sclera)),
            "lower_sclera": len(lower.overlap(sclera)),
            "upper_cornea": len(upper.overlap(cornea)),
            "lower_cornea": len(lower.overlap(cornea)),
            "upper_lower": len(upper.overlap(lower)),
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
    "unchanged_baseline_mesh_objects": sum(candidate.get(name) == value for name, value in baseline.items() if name not in lash_names),
    "rebuilt_lash_layers": 4,
    "topology": topology,
    "frames": frames,
    "non_finite_vertices": non_finite,
}
print("AEVRYND_LASHES_V38_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
