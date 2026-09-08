import json
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def input_path():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-hairline-v16.py -- model.blend")
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
hairline = bpy.data.objects.get("HairlineBaby")
failures = []
if not hairline:
    failures.append("HairlineBaby is missing")
if bpy.data.objects.get("HairlineFine"):
    failures.append("obsolete long HairlineFine layer remains")
report = {"frames": {}}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_tree(body, depsgraph)
    frame_report = {}
    for name in ("HairlineBaby", "HairMain", "HairGuides", "HairClumpsLarge", "HairFlyaways", "HairTempleClumps", "HairNapeClumps", "HairScalp"):
        obj = bpy.data.objects[name]
        overlaps = len(body_tree.overlap(world_tree(obj, depsgraph)))
        frame_report[name] = {"body_triangle_overlaps": overlaps}
        if overlaps:
            failures.append(f"frame {frame} {name} has {overlaps} body triangle overlaps")
    report["frames"][str(frame)] = frame_report

if hairline:
    roots = []
    for start in range(0, len(hairline.data.vertices), 10):
        roots.append(sum((hairline.matrix_world @ hairline.data.vertices[start + i].co for i in range(2)), Vector()) / 2)
    lengths = []
    for strand, root in enumerate(roots):
        tip = sum((hairline.matrix_world @ hairline.data.vertices[strand * 10 + 8 + i].co for i in range(2)), Vector()) / 2
        lengths.append((tip - root).length)
    report["hairline"] = {
        "strand_count": len(roots),
        "minimum_length_m": min(lengths),
        "maximum_length_m": max(lengths),
        "parent_bone": hairline.parent_bone,
    }
    if len(roots) != 84:
        failures.append(f"expected 84 short transition hairs, found {len(roots)}")
    if max(lengths) > 0.0095:
        failures.append(f"hairline strand too long: {max(lengths)}")
    if hairline.parent_bone != "head":
        failures.append("HairlineBaby is not parented to head")

print("AEVRYND_HAIRLINE_V16_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
