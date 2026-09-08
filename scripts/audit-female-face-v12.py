import json
import sys

import bpy
from mathutils.bvhtree import BVHTree


def input_path():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-face-v12.py -- model.blend")
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


def nearest_distance(source, target_tree, depsgraph):
    evaluated = source.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    values = []
    for vertex in mesh.vertices:
        point = evaluated.matrix_world @ vertex.co
        location, _, _, _ = target_tree.find_nearest(point)
        if location is not None:
            values.append((point - location).length)
    evaluated.to_mesh_clear()
    return min(values)


bpy.ops.wm.open_mainfile(filepath=input_path())
scene = bpy.context.scene
body = bpy.data.objects["AevryndFemaleBodyBase"]
report = {"frames": {}}
failures = []
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_tree(body, depsgraph)
    frame_report = {}
    for side in ("L", "R"):
        fold_name = f"Eye_{side}_UpperFold"
        fold = bpy.data.objects[fold_name]
        overlaps = len(body_tree.overlap(world_tree(fold, depsgraph)))
        frame_report[fold_name] = {"body_triangle_overlaps": overlaps}
        if overlaps:
            failures.append(f"frame {frame} {fold_name} has {overlaps} body triangle overlaps")

        catchlight_name = f"Eye_{side}_Catchlight"
        pupil_name = f"Eye_{side}_Pupil"
        catchlight = bpy.data.objects[catchlight_name]
        pupil_tree = world_tree(bpy.data.objects[pupil_name], depsgraph)
        distance = nearest_distance(catchlight, pupil_tree, depsgraph)
        frame_report[catchlight_name] = {"minimum_pupil_distance_m": distance}
        if distance > 0.0025:
            failures.append(f"frame {frame} {catchlight_name} is detached from the pupil")

    report["frames"][str(frame)] = frame_report

attribute = body.data.color_attributes.get("AevryndSkinTone")
report["skin_color_attribute"] = {
    "present": attribute is not None,
    "domain": attribute.domain if attribute else None,
    "data_type": attribute.data_type if attribute else None,
    "samples": len(attribute.data) if attribute else 0,
}
if attribute is None or attribute.domain != "POINT":
    failures.append("AevryndSkinTone point color attribute is missing")

print("AEVRYND_FACE_V12_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
