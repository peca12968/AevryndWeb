"""Render the r1050 selected face field and its two boundary loops."""

import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1051-mouth-boundary-diagnostic.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1051-mouth-boundary-diagnostic"
BODY = "AevryndFemaleCC0Baseline_v259"
CENTER_Z = 1.3862
RADIUS_X = 0.034
RADIUS_Z = 0.005
Y_MAX = -0.105


def connected(items, neighbours):
    remaining = set(items)
    groups = []
    while remaining:
        seed = remaining.pop()
        group = {seed}
        stack = [seed]
        while stack:
            fresh = neighbours(stack.pop()) & remaining
            remaining.difference_update(fresh)
            group.update(fresh)
            stack.extend(fresh)
        groups.append(group)
    return sorted(groups, key=len, reverse=True)


def mixed_world(body):
    blocks = body.data.shape_keys.key_blocks
    coords = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        relative = block.relative_key
        for index, item in enumerate(block.data):
            coords[index] += block.value * (item.co - relative.data[index].co)
    return [body.matrix_world @ coordinate for coordinate in coords]


def material(name, color):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1.0)
    result.use_nodes = True
    bsdf = next(node for node in result.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.28
    bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 0.25
    return result


def ordered_vertices(edges, points):
    adjacency = defaultdict(set)
    for first, second in edges:
        adjacency[first].add(second)
        adjacency[second].add(first)
    start = min(adjacency, key=lambda index: points[index].x)
    neighbours = sorted(adjacency[start], key=lambda index: points[index].z, reverse=True)
    result = [start]
    previous, current = start, neighbours[0]
    while current != start:
        result.append(current)
        following = adjacency[current] - {previous}
        previous, current = current, next(iter(following))
        if len(result) > len(adjacency):
            raise RuntimeError("boundary traversal failed")
    return result


def curve_loop(name, indices, points, loop_material):
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.00038
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(indices))
    for target, index in zip(spline.points, indices + [indices[0]]):
        target.co = (*points[index], 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(loop_material)
    return obj


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
points = mixed_world(body)
mesh = body.data
edge_faces = defaultdict(set)
face_edges = defaultdict(set)
for polygon in mesh.polygons:
    ids = list(polygon.vertices)
    for offset, first in enumerate(ids):
        edge = tuple(sorted((first, ids[(offset + 1) % len(ids)])))
        edge_faces[edge].add(polygon.index)
        face_edges[polygon.index].add(edge)
face_groups = connected(range(len(mesh.polygons)), lambda face: set().union(*(edge_faces[e] for e in face_edges[face])))
main = face_groups[0]
selected = set()
for face in main:
    polygon = mesh.polygons[face]
    center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
    ellipse = (center.x / RADIUS_X) ** 2 + ((center.z - CENTER_Z) / RADIUS_Z) ** 2
    if center.y < Y_MAX and ellipse < 1.0:
        selected.add(face)
boundary = {
    edge for face in selected for edge in face_edges[face]
    if len(edge_faces[edge] & selected) == 1 and bool(edge_faces[edge] - selected)
}
vertex_edges = defaultdict(set)
for edge in boundary:
    for vertex in edge:
        vertex_edges[vertex].add(edge)
loops = connected(boundary, lambda edge: set().union(*(vertex_edges[v] for v in edge)))

selection_material = material("Aevrynd_R1051_SelectedFaces", (0.75, 0.025, 0.018))
loop_materials = (
    material("Aevrynd_R1051_LoopA", (0.02, 0.85, 0.12)),
    material("Aevrynd_R1051_LoopB", (0.03, 0.25, 1.0)),
)
mesh.materials.append(selection_material)
selection_index = len(mesh.materials) - 1
for face in selected:
    mesh.polygons[face].material_index = selection_index
loop_objects = []
for loop_index, edges in enumerate(loops):
    order = ordered_vertices(edges, points)
    loop_objects.append(curve_loop(f"Aevrynd_R1051_Boundary_{loop_index}", order, points, loop_materials[loop_index]))

for obj in scene.objects:
    name = obj.name.lower()
    if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
        if not any(token in name for token in ("brow", "lash")) and obj not in loop_objects:
            obj.hide_render = True

OUT.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = 1100
scene.render.resolution_y = 760
scene.render.resolution_percentage = 100
camera = scene.camera
camera.data.lens = 135
views = (
    ("front", (0.0, -0.43, 1.388), (0.0, -0.115, 1.386)),
    ("left-oblique", (-0.115, -0.405, 1.392), (0.0, -0.117, 1.386)),
    ("right-oblique", (0.115, -0.405, 1.392), (0.0, -0.117, 1.386)),
)
renders = []
for label, location, target in views:
    camera.location = location
    look_at(camera, target)
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    renders.append(str(path))

report = {
    "revision": "v249r1051-mouth-boundary-diagnostic",
    "source": str(SOURCE),
    "selectedFaces": len(selected),
    "boundaryLoops": [len(loop) for loop in loops],
    "colors": {"selectedFaces": "red", "loop76": "green", "loop60": "blue"},
    "renders": renders,
    "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1051_DIAGNOSTIC=" + json.dumps(report, sort_keys=True))
