import json
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def input_path():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-groom-v14.py -- model.blend")
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


def roots(obj, stride, root_vertices):
    values = []
    for start in range(0, len(obj.data.vertices), stride):
        if start + root_vertices > len(obj.data.vertices):
            break
        values.append(sum(
            (obj.matrix_world @ obj.data.vertices[start + index].co for index in range(root_vertices)),
            Vector(),
        ) / root_vertices)
    return values


bpy.ops.wm.open_mainfile(filepath=input_path())
scene = bpy.context.scene
body = bpy.data.objects["AevryndFemaleBodyBase"]
layouts = {
    "HairClumpsLarge": (18, 2),
    "HairMain": (27, 3),
    "HairGuides": (27, 3),
    "HairlineFine": (21, 3),
    "HairFlyaways": (27, 3),
    "HairTempleClumps": (22, 2),
    "HairNapeClumps": (22, 2),
}
report = {"frames": {}}
failures = []
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_tree(body, depsgraph)
    frame_report = {}
    for name in (*layouts, "HairScalp", "Lip_Upper", "Lip_Lower"):
        obj = bpy.data.objects[name]
        overlaps = len(body_tree.overlap(world_tree(obj, depsgraph)))
        item = {"body_triangle_overlaps": overlaps}
        if name in layouts:
            stride, root_vertices = layouts[name]
            distances = []
            for point in roots(obj, stride, root_vertices):
                location, _, _, _ = body_tree.find_nearest(point)
                if location is not None:
                    distances.append((point - location).length)
            item.update({
                "root_count": len(distances),
                "minimum_root_distance_m": min(distances),
                "maximum_root_distance_m": max(distances),
            })
        frame_report[name] = item
        if overlaps:
            failures.append(f"frame {frame} {name} has {overlaps} body triangle overlaps")
    report["frames"][str(frame)] = frame_report

print("AEVRYND_GROOM_V14_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
