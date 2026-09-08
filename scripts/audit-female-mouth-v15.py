import json
import sys

import bpy
from mathutils.bvhtree import BVHTree


def input_path():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-mouth-v15.py -- model.blend")
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
names = ("Lip_Upper", "Lip_Lower", "Mouth_WetLine")
report = {"frames": {}, "weights": {}}
failures = []

for name in names:
    obj = bpy.data.objects[name]
    maximum = max((len(vertex.groups) for vertex in obj.data.vertices), default=0)
    unweighted = sum(not vertex.groups for vertex in obj.data.vertices)
    report["weights"][name] = {
        "maximum_influences": maximum,
        "unweighted_vertices": unweighted,
        "armature_modifiers": sum(modifier.type == "ARMATURE" for modifier in obj.modifiers),
    }
    if maximum > 4 or unweighted or report["weights"][name]["armature_modifiers"] != 1:
        failures.append(f"{name} has invalid skin binding")

for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_tree(body, depsgraph)
    frame_report = {}
    layer_trees = {}
    for name in names:
        tree = world_tree(bpy.data.objects[name], depsgraph)
        layer_trees[name] = tree
        overlaps = len(body_tree.overlap(tree))
        frame_report[name] = {"body_triangle_overlaps": overlaps}
        if overlaps:
            failures.append(f"frame {frame} {name} has {overlaps} body triangle overlaps")
    frame_report["upper_lower_seam_contacts"] = len(layer_trees["Lip_Upper"].overlap(layer_trees["Lip_Lower"]))
    frame_report["wet_line_upper_contacts"] = len(layer_trees["Mouth_WetLine"].overlap(layer_trees["Lip_Upper"]))
    frame_report["wet_line_lower_contacts"] = len(layer_trees["Mouth_WetLine"].overlap(layer_trees["Lip_Lower"]))
    report["frames"][str(frame)] = frame_report

print("AEVRYND_MOUTH_V15_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
