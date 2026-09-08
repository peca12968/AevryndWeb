import json
import math
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def input_path():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-rig.py -- model.blend")
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 1:
        raise SystemExit("expected one Blender file")
    return values[0]


def evaluated_surface(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    return BVHTree.FromObject(evaluated, depsgraph), evaluated.matrix_world, evaluated.matrix_world.inverted()


def distance_to_surface(surface_data, point):
    tree, matrix, inverse = surface_data
    location, _, _, _ = tree.find_nearest(inverse @ point)
    if location is None:
        return float("inf")
    return (point - matrix @ location).length


def root_distances(obj, vertices_per_strand, root_vertices, surface_data, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    values = []
    for start in range(0, len(obj.data.vertices), vertices_per_strand):
        if start + root_vertices > len(obj.data.vertices):
            break
        root = sum(
            (evaluated.matrix_world @ obj.data.vertices[start + index].co for index in range(root_vertices)),
            Vector(),
        ) / root_vertices
        values.append(distance_to_surface(surface_data, root))
    return values


def evaluated_positions(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    values = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    return values


bpy.ops.wm.open_mainfile(filepath=input_path())
scene = bpy.context.scene
body = bpy.data.objects["AevryndFemaleBodyBase"]
layouts = {
    "Eye_L_UpperLashes": (12, 4, 0.0030),
    "Eye_R_UpperLashes": (12, 4, 0.0030),
    "Eye_L_LowerLashes": (12, 4, 0.0030),
    "Eye_R_LowerLashes": (12, 4, 0.0030),
    "HairGuides": (14, 2, 0.0030),
    "HairMain": (14, 2, 0.0030),
    "HairlineFine": (6, 2, 0.0030),
}
report = {"frames": {}}
failures = []
frame_positions = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_surface = evaluated_surface(body, depsgraph)
    frame_report = {}
    for name, (stride, roots, limit) in layouts.items():
        values = root_distances(bpy.data.objects[name], stride, roots, body_surface, depsgraph)
        maximum = max(values)
        frame_report[name] = maximum
        if maximum > limit:
            failures.append(f"frame {frame} {name} root distance {maximum:.6f} m exceeds {limit:.4f} m")

    main_surface = evaluated_surface(bpy.data.objects["HairMain"], depsgraph)
    flyaway_values = root_distances(bpy.data.objects["HairFlyaways"], 14, 2, main_surface, depsgraph)
    frame_report["HairFlyawaysToHairMain"] = max(flyaway_values)
    if max(flyaway_values) > 0.0015:
        failures.append(f"frame {frame} flyaway roots detached from HairMain")

    positions = evaluated_positions(body, depsgraph)
    if any(not all(math.isfinite(value) for value in point) for point in positions):
        failures.append(f"frame {frame} body contains non-finite positions")
    frame_positions[frame] = positions
    report["frames"][str(frame)] = frame_report

if len(frame_positions[1]) != len(frame_positions[20]):
    failures.append("evaluated vertex count changed between deformation frames")
else:
    displacement = [(posed - neutral).length for neutral, posed in zip(frame_positions[1], frame_positions[20])]
    report["maximum_body_displacement_m"] = max(displacement)
    report["moved_vertices_over_1mm"] = sum(value > 0.001 for value in displacement)
    if report["maximum_body_displacement_m"] < 0.10:
        failures.append("pose suite did not create meaningful body deformation")
    if report["maximum_body_displacement_m"] > 0.75:
        failures.append("pose suite produced implausible body displacement")

print("AEVRYND_RIG_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
