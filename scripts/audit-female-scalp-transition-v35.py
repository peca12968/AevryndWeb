import hashlib
import json
import math
import struct
import sys

import bpy
from mathutils.bvhtree import BVHTree


def paths():
    values = sys.argv[sys.argv.index("--") + 1:]
    if len(values) != 2:
        raise SystemExit("expected baseline.blend candidate.blend")
    return values


def signatures(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    result = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        digest = hashlib.sha256()
        digest.update(struct.pack("<II", len(obj.data.vertices), len(obj.data.polygons)))
        for vertex in obj.data.vertices:
            digest.update(struct.pack("<fff", *vertex.co))
        for polygon in obj.data.polygons:
            digest.update(struct.pack("<I", len(polygon.vertices)))
            for index in polygon.vertices:
                digest.update(struct.pack("<I", index))
        result[obj.name] = digest.hexdigest()
    return result


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


baseline_path, candidate_path = paths()
baseline = signatures(baseline_path)
candidate = signatures(candidate_path)
failures = []
if baseline != candidate:
    failures.append("candidate geometry differs from collision-audited v33 baseline")

bpy.ops.wm.open_mainfile(filepath=candidate_path)
scene = bpy.context.scene
scalp = bpy.data.objects.get("HairScalp")
body = bpy.data.objects.get("AevryndFemaleBodyBase")
if scene.get("aevrynd_hair_revision") != 35:
    failures.append("scene hair revision is not 35")
if not scalp or not body:
    raise SystemExit("required scalp or body object is missing")
density = scalp.data.color_attributes.get("AevryndScalpDensity")
if not density or density.domain != "POINT":
    failures.append("exportable scalp density is missing")
alpha_range = [1.0, 0.0]
if density:
    for entry in density.data:
        alpha_range[0] = min(alpha_range[0], entry.color_srgb[3])
        alpha_range[1] = max(alpha_range[1], entry.color_srgb[3])
    if alpha_range[0] > 0.12 or alpha_range[1] < 0.99:
        failures.append(f"scalp density range is invalid: {alpha_range}")

material = scalp.data.materials[0]
shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
if material.surface_render_method != "DITHERED":
    failures.append("scalp material is not transparency enabled")
if not shader.inputs["Alpha"].links or not shader.inputs["Base Color"].links:
    failures.append("scalp density is not connected to both color and alpha")

hair_names = (
    "HairScalp", "HairUndercutScalp", "HairBoundaryClumps", "HairlineBaby",
    "HairMain", "HairGuides", "HairClumpsLarge", "HairFlyaways",
    "HairTempleClumps", "HairNapeClumps",
)
frames = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_bvh = world_tree(body, depsgraph)
    overlaps = {}
    for name in hair_names:
        count = len(body_bvh.overlap(world_tree(bpy.data.objects[name], depsgraph)))
        overlaps[name] = count
        if count:
            failures.append(f"frame {frame} {name} has {count} body triangle overlaps")
    frames[str(frame)] = overlaps

non_finite = sum(
    not all(math.isfinite(value) for value in vertex.co)
    for obj in bpy.data.objects if obj.type == "MESH" for vertex in obj.data.vertices
)
if non_finite:
    failures.append(f"candidate contains {non_finite} non-finite mesh vertices")

report = {
    "unchanged_mesh_objects": sum(candidate.get(name) == value for name, value in baseline.items()),
    "mesh_objects": len(baseline),
    "boundary_vertices": int(scalp["aevrynd_boundary_vertex_count"]),
    "fade_m": float(scalp["aevrynd_density_fade_m"]),
    "alpha_range": alpha_range,
    "hair_body_triangle_overlaps": frames,
    "non_finite_vertices": non_finite,
}
print("AEVRYND_SCALP_TRANSITION_V35_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
