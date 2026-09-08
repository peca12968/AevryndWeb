import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
candidate_path = Path(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v50.blend"
bpy.ops.wm.open_mainfile(filepath=str(candidate_path))
body = bpy.data.objects["AevryndFemaleBodyBase"]


def tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


def overlap_samples(first, second):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated_first = first.evaluated_get(depsgraph)
    evaluated_second = second.evaluated_get(depsgraph)
    mesh_first = evaluated_first.to_mesh()
    mesh_second = evaluated_second.to_mesh()
    points_first = [evaluated_first.matrix_world @ vertex.co for vertex in mesh_first.vertices]
    points_second = [evaluated_second.matrix_world @ vertex.co for vertex in mesh_second.vertices]
    tree_first = BVHTree.FromPolygons(points_first, [tuple(p.vertices) for p in mesh_first.polygons], all_triangles=False)
    tree_second = BVHTree.FromPolygons(points_second, [tuple(p.vertices) for p in mesh_second.polygons], all_triangles=False)
    pairs = tree_first.overlap(tree_second)
    samples = []
    for first_index, second_index in pairs[:8]:
        a = sum((points_first[index] for index in mesh_first.polygons[first_index].vertices), Vector()) / len(mesh_first.polygons[first_index].vertices)
        b = sum((points_second[index] for index in mesh_second.polygons[second_index].vertices), Vector()) / len(mesh_second.polygons[second_index].vertices)
        samples.append([(a.x + b.x) * 0.5, (a.y + b.y) * 0.5, (a.z + b.z) * 0.5])
    evaluated_first.to_mesh_clear()
    evaluated_second.to_mesh_clear()
    return len(pairs), samples


failures = []
required = {
    "Lip_Upper": (455, 384, "upper_lip_integrated"),
    "Lip_Lower": (455, 384, "lower_lip_integrated"),
    "Mouth_WetLine": (130, 64, "mouth_wet_margin"),
    "Mouth_OralCavity": (193, 192, "oral_cavity_cup"),
}
objects = {}
for name, (vertices, faces, role) in required.items():
    obj = bpy.data.objects.get(name)
    if obj is None:
        failures.append(name + " missing")
        continue
    objects[name] = {"vertices": len(obj.data.vertices), "faces": len(obj.data.polygons), "role": obj.get("aevrynd_role")}
    if len(obj.data.vertices) != vertices or len(obj.data.polygons) != faces or obj.get("aevrynd_role") != role:
        failures.append(name + " topology or role invalid")
    if name.startswith("Lip_") or name == "Mouth_WetLine":
        if obj.parent_type != "OBJECT" or not any(modifier.type == "ARMATURE" for modifier in obj.modifiers):
            failures.append(name + " skinned binding invalid")
        if name.startswith("Lip_") and (obj.get("aevrynd_profile_rows") != 7 or obj.get("aevrynd_skin_transition_rows") != 2):
            failures.append(name + " profile metadata invalid")
    elif obj.parent_type != "BONE" or obj.parent_bone != "head":
        failures.append(name + " head binding invalid")

if body.get("aevrynd_mouth_opening_state") != "open_subdivided_topology":
    failures.append("body mouth opening state invalid")
if body.get("aevrynd_mouth_opening_faces_removed") != 44:
    failures.append("unexpected mouth opening face count")
if any(modifier.type == "MULTIRES" for modifier in body.modifiers):
    failures.append("baked body still has Multires")

bm = bmesh.new()
bm.from_mesh(body.data)
boundary = [edge for edge in bm.edges if edge.is_boundary]
mouth_boundary = []
for edge in boundary:
    center = body.matrix_world @ ((edge.verts[0].co + edge.verts[1].co) * 0.5)
    if abs(center.x) < 0.030 and 1.530 < center.z < 1.539 and center.y < -0.120:
        mouth_boundary.append(edge)
remaining = set(mouth_boundary)
components = 0
while remaining:
    components += 1
    stack = [remaining.pop()]
    while stack:
        current = stack.pop()
        linked = [edge for vertex in current.verts for edge in vertex.link_edges if edge in remaining]
        for edge in linked:
            remaining.remove(edge)
            stack.append(edge)
bm.free()
if components != 2 or len(mouth_boundary) < 12:
    failures.append(f"mouth boundary invalid components={components} edges={len(mouth_boundary)}")

weight_report = {"unweighted": 0, "over_four": 0, "maximum": 0}
for vertex in body.data.vertices:
    count = sum(element.weight > 1e-8 for element in vertex.groups)
    weight_report["maximum"] = max(weight_report["maximum"], count)
    weight_report["unweighted"] += count == 0
    weight_report["over_four"] += count > 4
if weight_report["unweighted"] or weight_report["over_four"]:
    failures.append("body skin weights invalid")

frames = {}
pairs = (
    ("body_upper", body, bpy.data.objects["Lip_Upper"]),
    ("body_lower", body, bpy.data.objects["Lip_Lower"]),
    ("body_wetline", body, bpy.data.objects["Mouth_WetLine"]),
    ("body_cavity", body, bpy.data.objects["Mouth_OralCavity"]),
    ("upper_lower", bpy.data.objects["Lip_Upper"], bpy.data.objects["Lip_Lower"]),
    ("upper_wetline", bpy.data.objects["Lip_Upper"], bpy.data.objects["Mouth_WetLine"]),
    ("lower_wetline", bpy.data.objects["Lip_Lower"], bpy.data.objects["Mouth_WetLine"]),
)
for frame in (1, 20):
    bpy.context.scene.frame_set(frame)
    values = {}
    for label, first, second in pairs:
        if label == "upper_lower":
            count, samples = overlap_samples(first, second)
            values[label + "_samples"] = samples
        else:
            count = len(tree(first).overlap(tree(second)))
        values[label] = count
        if count:
            failures.append(f"frame {frame} {label} has {count} triangle overlaps")
    frames[str(frame)] = values

nonfinite = 0
for obj in (body, *[bpy.data.objects[name] for name in required]):
    nonfinite += sum(not all(math.isfinite(value) for value in vertex.co) for vertex in obj.data.vertices)
if nonfinite:
    failures.append("nonfinite coordinates")

report = {
    "status": "PASS" if not failures else "FAIL",
    "body": {"vertices": len(body.data.vertices), "faces": len(body.data.polygons)},
    "mouth_boundary": {"edges": len(mouth_boundary), "components": components},
    "weights": weight_report,
    "objects": objects,
    "frames": frames,
    "nonfinite": nonfinite,
    "failures": failures,
}
print("AEVRYND_MOUTH_TOPOLOGY_V50_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit(1)
