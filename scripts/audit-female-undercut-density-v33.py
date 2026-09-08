import json
import math
import hashlib
import struct
import sys

import bpy
from mathutils.bvhtree import BVHTree


def input_paths():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-undercut-density-v33.py -- [baseline.blend] model.blend")
    values = sys.argv[sys.argv.index("--") + 1:]
    if len(values) not in (1, 2):
        raise SystemExit("expected candidate, or baseline and candidate Blender files")
    return (None, values[0]) if len(values) == 1 else tuple(values)


def geometry_signatures(path):
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


baseline_path, candidate_path = input_paths()
baseline_geometry = geometry_signatures(baseline_path) if baseline_path else None
bpy.ops.wm.open_mainfile(filepath=candidate_path)
candidate_geometry = geometry_signatures(candidate_path)
scene = bpy.context.scene
body = bpy.data.objects["AevryndFemaleBodyBase"]
undercut = bpy.data.objects.get("HairUndercutScalp")
failures = []
unchanged_mesh_objects = None
if baseline_geometry is not None:
    expected = set(baseline_geometry) | {"HairUndercutScalp"}
    if set(candidate_geometry) != expected:
        failures.append("candidate mesh object set is not baseline plus the undercut layer")
    unchanged_mesh_objects = sum(
        candidate_geometry.get(name) == signature
        for name, signature in baseline_geometry.items()
    )
    if unchanged_mesh_objects != len(baseline_geometry):
        failures.append(
            f"only {unchanged_mesh_objects}/{len(baseline_geometry)} baseline mesh objects are unchanged"
        )
if not undercut:
    raise SystemExit("HairUndercutScalp is missing")
if scene.get("aevrynd_hair_revision") != 33:
    failures.append("scene hair revision is not 33")
if undercut.get("aevrynd_role") != "hair_undercut_scalp":
    failures.append("undercut role is invalid")
if len(undercut.data.vertices) != 1080 or len(undercut.data.polygons) != 994:
    failures.append("undercut topology is invalid")
if undercut.get("aevrynd_projection_misses") != 0:
    failures.append("undercut surface projection missed the body")

maximum_influences = max((len(vertex.groups) for vertex in undercut.data.vertices), default=0)
unweighted = sum(not vertex.groups for vertex in undercut.data.vertices)
armatures = sum(modifier.type == "ARMATURE" for modifier in undercut.modifiers)
if maximum_influences > 4 or unweighted or armatures != 1:
    failures.append("undercut skin binding is invalid")

density = undercut.data.color_attributes.get("AevryndUndercutDensity")
if not density or density.domain != "POINT":
    failures.append("exportable undercut density is missing")
alpha_range = [1.0, 0.0]
if density:
    for entry in density.data:
        alpha_range[0] = min(alpha_range[0], entry.color_srgb[3])
        alpha_range[1] = max(alpha_range[1], entry.color_srgb[3])
    if alpha_range[0] > 0.02 or not 0.50 <= alpha_range[1] <= 0.62:
        failures.append(f"undercut density fade is invalid: {alpha_range}")

hair_names = (
    "HairScalp", "HairBoundaryClumps", "HairlineBaby", "HairMain",
    "HairGuides", "HairClumpsLarge", "HairFlyaways", "HairTempleClumps",
    "HairNapeClumps",
)
frames = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    undercut_tree = world_tree(undercut, depsgraph)
    body_overlaps = len(undercut_tree.overlap(world_tree(body, depsgraph)))
    layer_overlaps = {}
    if body_overlaps:
        failures.append(f"frame {frame} undercut has {body_overlaps} body overlaps")
    for name in hair_names:
        overlaps = len(undercut_tree.overlap(world_tree(bpy.data.objects[name], depsgraph)))
        layer_overlaps[name] = overlaps
        if overlaps:
            failures.append(f"frame {frame} undercut has {overlaps} overlaps with {name}")
    frames[str(frame)] = {
        "body_triangle_overlaps": body_overlaps,
        "hair_layer_triangle_overlaps": layer_overlaps,
    }

non_finite = sum(
    not all(math.isfinite(value) for value in vertex.co)
    for vertex in undercut.data.vertices
)
if non_finite:
    failures.append(f"undercut contains {non_finite} non-finite vertices")

report = {
    "vertices": len(undercut.data.vertices),
    "faces": len(undercut.data.polygons),
    "maximum_influences": maximum_influences,
    "unweighted_vertices": unweighted,
    "alpha_range": alpha_range,
    "frames": frames,
    "non_finite_vertices": non_finite,
    "unchanged_baseline_mesh_objects": unchanged_mesh_objects,
}
print("AEVRYND_UNDERCUT_DENSITY_V33_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
