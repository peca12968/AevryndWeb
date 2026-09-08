import json
import math
import sys

import bpy
from mathutils.bvhtree import BVHTree


def input_path():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-eyes-v20.py -- model.blend")
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
failures = []
if scene.get("aevrynd_eye_revision") != 20 or body.get("aevrynd_eye_revision") != 20:
    failures.append("eye revision is not 20")
orbit_vertices = int(body.get("aevrynd_orbit_vertices", 0))
maximum_delta = float(body.get("aevrynd_orbit_max_delta_m", 0.0))
if orbit_vertices < 800:
    failures.append(f"too few orbit vertices changed: {orbit_vertices}")
if not 0.0009 <= maximum_delta <= 0.0013:
    failures.append(f"orbit delta outside guarded range: {maximum_delta}")

frames = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_tree(body, depsgraph)
    frame_report = {}
    for side in ("L", "R"):
        for suffix in ("UpperFold", "UpperLashes", "LowerLashes", "TearMeniscus", "IrisFibers"):
            name = f"Eye_{side}_{suffix}"
            obj = bpy.data.objects.get(name)
            if not obj:
                failures.append(f"{name} is missing")
                continue
            overlaps = len(body_tree.overlap(world_tree(obj, depsgraph)))
            frame_report[name] = {"body_triangle_overlaps": overlaps}
            if overlaps:
                failures.append(f"frame {frame} {name} has {overlaps} body triangle overlaps")
    frames[str(frame)] = frame_report

fiber_report = {}
for side in ("L", "R"):
    fiber = bpy.data.objects.get(f"Eye_{side}_IrisFibers")
    cornea = bpy.data.objects.get(f"Eye_{side}_Cornea")
    catchlight = bpy.data.objects.get(f"Eye_{side}_Catchlight")
    if cornea and cornea.hide_render:
        failures.append(f"{cornea.name} is hidden from render")
    if fiber:
        fiber_report[fiber.name] = {
            "vertices": len(fiber.data.vertices),
            "faces": len(fiber.data.polygons),
            "materials": len(fiber.data.materials),
            "parent_bone": fiber.parent_bone,
        }
        if len(fiber.data.polygons) != 52 or fiber.parent_bone != "head":
            failures.append(f"{fiber.name} topology or parent regressed")
    if catchlight:
        maximum_dimension = max(catchlight.dimensions)
        if maximum_dimension > 0.0010:
            failures.append(f"{catchlight.name} is still oversized: {maximum_dimension}")

non_finite = 0
for name in ("Eye_L_IrisFibers", "Eye_R_IrisFibers"):
    for vertex in bpy.data.objects[name].data.vertices:
        if not all(math.isfinite(value) for value in vertex.co):
            non_finite += 1
if non_finite:
    failures.append(f"iris fibers contain {non_finite} non-finite vertices")

report = {
    "orbit_vertices": orbit_vertices,
    "maximum_orbit_delta_m": maximum_delta,
    "frames": frames,
    "iris_fibers": fiber_report,
    "non_finite_iris_vertices": non_finite,
}
print("AEVRYND_EYES_V20_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
