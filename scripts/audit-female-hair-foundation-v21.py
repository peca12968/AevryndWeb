import json
import sys

import bpy
from mathutils.bvhtree import BVHTree


def input_path():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-hair-foundation-v21.py -- model.blend")
    values = sys.argv[sys.argv.index("--") + 1:]
    if len(values) != 1:
        raise SystemExit("expected one Blender file")
    return values[0]


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


bpy.ops.wm.open_mainfile(filepath=input_path())
scene = bpy.context.scene
body = bpy.data.objects["AevryndFemaleBodyBase"]
scalp = bpy.data.objects.get("HairScalp")
boundary = bpy.data.objects.get("HairBoundaryClumps")
failures = []
if scene.get("aevrynd_hair_revision") != 21:
    failures.append("hair revision is not 21")
if not scalp:
    failures.append("HairScalp is missing")
if not boundary:
    failures.append("HairBoundaryClumps is missing")

scalp_report = {}
if scalp:
    scalp_report = {
        "vertices": len(scalp.data.vertices),
        "faces": len(scalp.data.polygons),
        "clearance_m": float(scalp.get("aevrynd_clearance_m", 0.0)),
        "projection_misses": int(scalp.get("aevrynd_projection_misses", -1)),
        "parent_bone": scalp.parent_bone,
    }
    if len(scalp.data.vertices) != 2497 or len(scalp.data.polygons) != 2496:
        failures.append("scalp topology regressed")
    if scalp_report["projection_misses"] != 0 or scalp.parent_bone != "head":
        failures.append("scalp projection or attachment regressed")

boundary_report = {}
if boundary:
    boundary_report = {
        "vertices": len(boundary.data.vertices),
        "faces": len(boundary.data.polygons),
        "clumps": int(boundary.get("aevrynd_clump_count", 0)),
        "clearance_m": float(boundary.get("aevrynd_clearance_m", 0.0)),
        "parent_bone": boundary.parent_bone,
    }
    if boundary_report["clumps"] < 50 or boundary.parent_bone != "head":
        failures.append("boundary clump density or attachment regressed")

frames = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_tree(body, depsgraph)
    frame_report = {}
    for obj in (scalp, boundary):
        if not obj:
            continue
        overlaps = len(body_tree.overlap(world_tree(obj, depsgraph)))
        frame_report[obj.name] = {"body_triangle_overlaps": overlaps}
        if overlaps:
            failures.append(f"frame {frame} {obj.name} has {overlaps} body triangle overlaps")
    frames[str(frame)] = frame_report

report = {"scalp": scalp_report, "boundary": boundary_report, "frames": frames}
print("AEVRYND_HAIR_FOUNDATION_V21_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
