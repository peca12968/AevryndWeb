import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


candidate_path = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
baseline_path = candidate_path.parent / "aevrynd-female-authoring-v52.blend"
removed = {"HairMain", "HairGuides", "HairFlyaways", "HairClumpsLarge", "HairClumpsMediumCards"}
added = {"HairFiberBase", "HairFiberDetail", "HairFiberLOD1"}


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
    bpy.ops.wm.open_mainfile(filepath=str(path))
    return {obj.name: signature(obj) for obj in bpy.data.objects if obj.type == "MESH"}


baseline = snapshot(baseline_path)
candidate = snapshot(candidate_path)
failures = []
expected = (set(baseline) - removed) | added
if set(candidate) != expected:
    failures.append("mesh set mismatch")
unexpected = [name for name, value in baseline.items() if name not in removed and candidate.get(name) != value]
if unexpected:
    failures.append("unexpected geometry: " + ",".join(unexpected))


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


expected_geometry = {
    "HairFiberBase": (1850, 37000, 16650, "hair_fiber_base"),
    "HairFiberDetail": (725, 14500, 6525, "hair_fiber_detail"),
    "HairFiberLOD1": (588, 11760, 5292, "hair_fiber_lod1"),
}
geometry = {}
for name, (strands, vertices, faces, role) in expected_geometry.items():
    obj = bpy.data.objects[name]
    geometry[name] = {
        "strands": int(obj.get("aevrynd_strand_count", 0)),
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
        "role": obj.get("aevrynd_role"),
        "root_clearance_m": float(obj.get("aevrynd_root_clearance_m", 0.0)),
        "free_body_clearance_m": float(obj.get("aevrynd_minimum_free_body_clearance_m", 0.0)),
        "materials": [material.name for material in obj.data.materials if material],
        "uv_layers": len(obj.data.uv_layers),
        "parent_bone": obj.parent_bone,
    }
    if geometry[name]["strands"] != strands or geometry[name]["vertices"] != vertices or geometry[name]["faces"] != faces:
        failures.append(name + " geometry mismatch")
    if geometry[name]["role"] != role or geometry[name]["uv_layers"] != 1 or geometry[name]["parent_bone"] != "head":
        failures.append(name + " layer contract mismatch")
    if geometry[name]["root_clearance_m"] < 0.001 or geometry[name]["free_body_clearance_m"] < 0.003:
        failures.append(name + " clearance mismatch")
    if geometry[name]["materials"] != ["Aevrynd_Hair_Strands_v55"]:
        failures.append(name + " material mismatch")

image = bpy.data.images.get("AevryndHairStrandAlphaV55")
if image is None or tuple(image.size) != (192, 768) or not image.packed_file:
    failures.append("packed strand texture mismatch")

scalp = bpy.data.objects["HairScalp"]
density = scalp.data.color_attributes.get("AevryndScalpDensity")
if density is None:
    failures.append("scalp density missing")
    scalp_color = {}
else:
    values = [item.color_srgb[:] for item in density.data]
    scalp_color = {
        "rgb_min": [min(value[index] for value in values) for index in range(3)],
        "rgb_max": [max(value[index] for value in values) for index in range(3)],
        "alpha_min": min(value[3] for value in values),
        "alpha_max": max(value[3] for value in values),
    }
    if max(scalp_color["rgb_max"]) > 0.026 or scalp_color["alpha_min"] > 0.11 or scalp_color["alpha_max"] < 0.99:
        failures.append("scalp density range mismatch")

scene = bpy.context.scene
frames = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(bpy.data.objects["AevryndFemaleBodyBase"], depsgraph)
    undercut_tree = tree(bpy.data.objects["HairUndercutScalp"], depsgraph)
    scalp_tree = tree(bpy.data.objects["HairScalp"], depsgraph)
    values = {}
    for name in sorted(added):
        hair_tree = tree(bpy.data.objects[name], depsgraph)
        body_overlap = len(body_tree.overlap(hair_tree))
        undercut_overlap = len(undercut_tree.overlap(hair_tree))
        scalp_overlap = len(scalp_tree.overlap(hair_tree))
        values[name] = {"body": body_overlap, "undercut": undercut_overlap, "scalp": scalp_overlap}
        if body_overlap or undercut_overlap or scalp_overlap:
            failures.append(
                f"frame {frame} {name} collision "
                f"body={body_overlap}/undercut={undercut_overlap}/scalp={scalp_overlap}"
            )
    frames[str(frame)] = values

nonfinite = sum(
    not all(math.isfinite(value) for value in vertex.co)
    for obj in bpy.data.objects if obj.type == "MESH"
    for vertex in obj.data.vertices
)
if nonfinite:
    failures.append(f"nonfinite {nonfinite}")

report = {
    "status": "PASS" if not failures else "FAIL",
    "unchanged_baseline_meshes": sum(candidate.get(name) == value for name, value in baseline.items() if name not in removed),
    "removed": sorted(removed),
    "added": sorted(added),
    "geometry": geometry,
    "scalp_color": scalp_color,
    "frames": frames,
    "nonfinite": nonfinite,
    "failures": failures,
}
print("AEVRYND_STRAND_GROOM_V55_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit(1)
