import hashlib
import json
import math
import struct
import sys

import bpy
from mathutils.bvhtree import BVHTree


def input_paths():
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


baseline_path, candidate_path = input_paths()
baseline = snapshot(baseline_path)
candidate = snapshot(candidate_path)
failures = []
changed_names = {"Brow_L", "Brow_R"}
density_names = {"Brow_L_Density", "Brow_R_Density"}
if set(candidate) != set(baseline) | density_names:
    failures.append("candidate object set is not baseline plus two brow-density layers")
unexpected = [name for name, value in baseline.items() if name not in changed_names and candidate.get(name) != value]
if unexpected:
    failures.append(f"unexpected geometry changes: {unexpected}")

bpy.ops.wm.open_mainfile(filepath=candidate_path)
scene = bpy.context.scene
if scene.get("aevrynd_face_revision") != 39:
    failures.append("scene face revision is not 39")
topology = {}
for side in ("L", "R"):
    brow = bpy.data.objects[f"Brow_{side}"]
    density_obj = bpy.data.objects[f"Brow_{side}_Density"]
    minimum = float(brow["aevrynd_length_min_m"])
    maximum = float(brow["aevrynd_length_max_m"])
    topology[brow.name] = {
        "fibers": int(brow["aevrynd_fiber_count"]),
        "vertices": len(brow.data.vertices),
        "faces": len(brow.data.polygons),
        "length_range_m": [minimum, maximum],
    }
    if int(brow["aevrynd_fiber_count"]) != 120 or len(brow.data.vertices) != 1800 or len(brow.data.polygons) != 1440:
        failures.append(f"{brow.name} topology is invalid")
    if not 0.0028 <= minimum <= 0.0032 or not 0.0090 <= maximum <= 0.0098:
        failures.append(f"{brow.name} length range is invalid")
    if len(density_obj.data.vertices) != 175 or len(density_obj.data.polygons) != 136:
        failures.append(f"{density_obj.name} topology is invalid")
    density = density_obj.data.color_attributes.get("AevryndBrowDensity")
    if not density or density.domain != "POINT":
        failures.append(f"{density_obj.name} exportable density is missing")
    else:
        alpha = [entry.color_srgb[3] for entry in density.data]
        if min(alpha) > 0.03 or not 0.40 <= max(alpha) <= 0.44:
            failures.append(f"{density_obj.name} alpha range is invalid")
    for obj in (brow, density_obj):
        if obj.parent_type != "BONE" or obj.parent_bone != "head":
            failures.append(f"{obj.name} is not bound to the head bone")

body = bpy.data.objects["AevryndFemaleBodyBase"]
frames = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_bvh = world_tree(body, depsgraph)
    values = {}
    for side in ("L", "R"):
        brow = world_tree(bpy.data.objects[f"Brow_{side}"], depsgraph)
        density_obj = world_tree(bpy.data.objects[f"Brow_{side}_Density"], depsgraph)
        side_values = {
            "fiber_body": len(brow.overlap(body_bvh)),
            "density_body": len(density_obj.overlap(body_bvh)),
            "fiber_density": len(brow.overlap(density_obj)),
        }
        values[side] = side_values
        for label, count in side_values.items():
            if count:
                failures.append(f"frame {frame} brow {side} {label} has {count} triangle overlaps")
    frames[str(frame)] = values

non_finite = sum(
    not all(math.isfinite(value) for value in vertex.co)
    for obj in bpy.data.objects if obj.type == "MESH" for vertex in obj.data.vertices
)
if non_finite:
    failures.append(f"candidate contains {non_finite} non-finite vertices")
report = {
    "unchanged_baseline_mesh_objects": sum(candidate.get(name) == value for name, value in baseline.items() if name not in changed_names),
    "rebuilt_brow_layers": 2,
    "new_density_layers": 2,
    "topology": topology,
    "frames": frames,
    "non_finite_vertices": non_finite,
}
print("AEVRYND_BROWS_V39_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
