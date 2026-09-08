import json
import sys

import bpy
from mathutils.bvhtree import BVHTree


def input_path():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-clothing.py -- model.blend")
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 1:
        raise SystemExit("expected one Blender file")
    return values[0]


def body_surface(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    return BVHTree.FromObject(evaluated, depsgraph), evaluated.matrix_world, evaluated.matrix_world.inverted()


def triangle_overlaps(obj, body_tree, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    garment_tree = BVHTree.FromObject(evaluated, depsgraph)
    return len(body_tree.overlap(garment_tree))


def signed_distances(obj, surface_data, depsgraph):
    tree, body_matrix, body_inverse = surface_data
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    values = []
    for vertex in mesh.vertices:
        world = evaluated.matrix_world @ vertex.co
        location, normal, _, _ = tree.find_nearest(body_inverse @ world)
        if location is None:
            continue
        surface_world = body_matrix @ location
        normal_world = (body_matrix.inverted().transposed().to_3x3() @ normal).normalized()
        radial = world.copy()
        radial.x -= body_matrix.translation.x
        radial.y -= body_matrix.translation.y
        radial.z = 0.0
        if radial.length > 1e-6 and normal_world.dot(radial) < 0.0:
            normal_world.negate()
        values.append(((world - surface_world).dot(normal_world), tuple(world)))
    evaluated.to_mesh_clear()
    return values


bpy.ops.wm.open_mainfile(filepath=input_path())
scene = bpy.context.scene
body = bpy.data.objects["AevryndFemaleBodyBase"]
garments = [bpy.data.objects["Clothing_InnerTop"], bpy.data.objects["Clothing_InnerShorts"]]
report = {"frames": {}}
failures = []
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    surface = body_surface(body, depsgraph)
    frame_report = {}
    for garment in garments:
        values = signed_distances(garment, surface, depsgraph)
        signed = [value for value, _ in values]
        worst_value, worst_point = min(values, key=lambda item: item[0])
        item = {
            "samples": len(values),
            "minimum_signed_distance_m": worst_value,
            "minimum_sample_world": worst_point,
            "penetrating_samples": sum(value <= 0.0 for value in signed),
            "samples_below_1mm": sum(value < 0.001 for value in signed),
            "triangle_overlaps": triangle_overlaps(garment, surface[0], depsgraph),
        }
        frame_report[garment.name] = item
        if item["triangle_overlaps"]:
            failures.append(f"frame {frame} {garment.name} has {item['triangle_overlaps']} triangle overlaps")
    report["frames"][str(frame)] = frame_report

print("AEVRYND_CLOTHING_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
