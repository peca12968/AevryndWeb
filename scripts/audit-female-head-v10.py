import json
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def input_path():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-head-v10.py -- model.blend")
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


def vertex_distances(obj, target_tree, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    values = []
    for vertex in mesh.vertices:
        point = evaluated.matrix_world @ vertex.co
        location, _, _, _ = target_tree.find_nearest(point)
        if location is not None:
            values.append((point - location).length)
    evaluated.to_mesh_clear()
    return values


def fiber_root_distances(fibers, main):
    values = []
    stride = 14
    for fiber_index, start in enumerate(range(0, len(fibers.data.vertices), stride)):
        root = sum(
            (fibers.matrix_world @ fibers.data.vertices[start + index].co for index in (0, 1)),
            Vector(),
        ) / 2
        main_start = (fiber_index // 2) * stride
        main_root = sum(
            (main.matrix_world @ main.data.vertices[main_start + index].co for index in (0, 1)),
            Vector(),
        ) / 2
        values.append((root - main_root).length)
    return values


bpy.ops.wm.open_mainfile(filepath=input_path())
scene = bpy.context.scene
body = bpy.data.objects["AevryndFemaleBodyBase"]
checked = [
    bpy.data.objects["HairScalp"],
    bpy.data.objects["HairMain"],
    bpy.data.objects["HairlineFine"],
    bpy.data.objects["HairFiberDetail"],
    bpy.data.objects["Lip_Upper"],
    bpy.data.objects["Lip_Lower"],
]
report = {"frames": {}}
failures = []
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_tree(body, depsgraph)
    frame_report = {}
    for obj in checked:
        obj_tree = world_tree(obj, depsgraph)
        distances = vertex_distances(obj, body_tree, depsgraph)
        overlap_pairs = body_tree.overlap(obj_tree)
        overlaps = len(overlap_pairs)
        frame_report[obj.name] = {
            "vertices": len(distances),
            "minimum_body_distance_m": min(distances),
            "maximum_body_distance_m": max(distances),
            "body_triangle_overlaps": overlaps,
            "overlap_object_triangles_sample": [pair[1] for pair in overlap_pairs[:20]],
        }
        if overlaps:
            failures.append(f"frame {frame} {obj.name} has {overlaps} body triangle overlaps")
    fiber_roots = fiber_root_distances(
        bpy.data.objects["HairFiberDetail"], bpy.data.objects["HairMain"]
    )
    frame_report["HairFiberDetail"]["fiber_root_count"] = len(fiber_roots)
    frame_report["HairFiberDetail"]["maximum_main_root_distance_m"] = max(fiber_roots)
    if max(fiber_roots) > 0.0010:
        failures.append(f"frame {frame} fiber roots detached by {max(fiber_roots):.6f} m")
    report["frames"][str(frame)] = frame_report

print("AEVRYND_HEAD_V10_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
