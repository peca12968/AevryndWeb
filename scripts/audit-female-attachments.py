import json
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def arguments():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-attachments.py -- model.blend")
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 1:
        raise SystemExit("expected one Blender file")
    return values[0]


def surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    return BVHTree.FromObject(evaluated, depsgraph), evaluated.matrix_world, evaluated.matrix_world.inverted()


def distance_to_surface(surface_data, point):
    tree, matrix, inverse = surface_data
    location, _, _, _ = tree.find_nearest(inverse @ point)
    if location is None:
        return float("inf")
    return (point - matrix @ location).length


def root_distances(obj, vertices_per_strand, root_vertices, surface_data):
    values = []
    for start in range(0, len(obj.data.vertices), vertices_per_strand):
        if start + root_vertices > len(obj.data.vertices):
            break
        root = sum(
            (obj.matrix_world @ obj.data.vertices[start + index].co for index in range(root_vertices)),
            Vector(),
        ) / root_vertices
        values.append(distance_to_surface(surface_data, root))
    return values


bpy.ops.wm.open_mainfile(filepath=arguments())
body = bpy.data.objects["AevryndFemaleBodyBase"]
surface_data = surface(body)
layouts = {
    "Eye_L_UpperLashes": (12, 4),
    "Eye_R_UpperLashes": (12, 4),
    "Eye_L_LowerLashes": (12, 4),
    "Eye_R_LowerLashes": (12, 4),
    "HairGuides": (14, 2),
    "HairMain": (14, 2),
    "HairlineFine": (6, 2),
}
report = {}
failures = []
for name, (stride, roots) in layouts.items():
    obj = bpy.data.objects[name]
    distances = root_distances(obj, stride, roots, surface_data)
    maximum = max(distances)
    report[name] = {
        "root_count": len(distances),
        "minimum_distance_m": min(distances),
        "maximum_distance_m": maximum,
    }
    if maximum > 0.0022:
        failures.append(f"{name} maximum root distance {maximum:.6f} m exceeds 0.0022 m")

flyaway_surface = surface(bpy.data.objects["HairMain"])
flyaway_distances = root_distances(bpy.data.objects["HairFlyaways"], 14, 2, flyaway_surface)
flyaway_maximum = max(flyaway_distances)
report["HairFlyaways"] = {
    "attachment_target": "HairMain",
    "root_count": len(flyaway_distances),
    "minimum_distance_m": min(flyaway_distances),
    "maximum_distance_m": flyaway_maximum,
}
if flyaway_maximum > 0.0015:
    failures.append(f"HairFlyaways maximum parent distance {flyaway_maximum:.6f} m exceeds 0.0015 m")

print("AEVRYND_ATTACHMENT_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
