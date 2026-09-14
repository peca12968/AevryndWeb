import bmesh
import json
import math
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-layered-front-locks-r517.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-eye-ratio-r520.blend"
REPORT = ASSETS / "female-v249-mainline-natural-eye-ratio-r520.build-report.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {
    "L": {"x": 0.03453, "z": 1.60780, "outer_sign": 1.0},
    "R": {"x": -0.03444, "z": 1.60780, "outer_sign": -1.0},
}
OPTICAL = tuple(f"Eye_{side}_{part}" for side in ("L", "R") for part in ("Cornea", "Sclera"))
FRAMES = (1, 20, 33, 61)
STRENGTH = 0.50
IRIS_SCALE = (0.85, 0.65, 0.60)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def boundary_components(mesh):
    counts = defaultdict(int)
    adjacency = defaultdict(set)
    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for index, first in enumerate(vertices):
            second = vertices[(index + 1) % len(vertices)]
            counts[tuple(sorted((first, second)))] += 1
    for (first, second), count in counts.items():
        if count == 1:
            adjacency[first].add(second)
            adjacency[second].add(first)
    result, unseen = [], set(adjacency)
    while unseen:
        start = unseen.pop()
        component, queue = {start}, deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor not in component:
                    component.add(neighbor)
                    unseen.discard(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
world_points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
evaluated.to_mesh_clear()

components = boundary_components(body.data)
boundaries = {}
for side, eye in EYES.items():
    matches = []
    for component in components:
        center = sum((world_points[index] for index in component), Vector()) / len(component)
        if abs(center.x - eye["x"]) < 0.018 and center.y < -0.075 and abs(center.z - eye["z"]) < 0.020:
            matches.append(component)
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {side} eye boundary, found {len(matches)}")
    boundaries[side] = matches[0]

boundary_deltas = {}
for side, eye in EYES.items():
    points = [world_points[index] for index in boundaries[side]]
    half_width = max(abs(point.x - eye["x"]) for point in points)
    for index in boundaries[side]:
        point = world_points[index]
        q = clamp((point.x - eye["x"]) / half_width, -1.0, 1.0)
        anatomical_q = q * eye["outer_sign"]
        arch = max(0.0, 1.0 - abs(q) ** 1.55)
        middle = eye["z"] + 0.00012 + 0.00045 * anatomical_q
        if point.z >= eye["z"]:
            target_z = middle + 0.00018 + 0.00375 * arch
        else:
            target_z = middle - 0.00012 - 0.00305 * arch
        canthus_fade = 1.0 - smoothstep((abs(q) - 0.84) / 0.16)
        boundary_deltas[index] = (target_z - point.z) * canthus_fade

deltas = {}
for side, eye in EYES.items():
    boundary_points = [(index, world_points[index]) for index in boundaries[side]]
    for index, point in enumerate(world_points):
        if abs(point.x - eye["x"]) > 0.026 or abs(point.z - eye["z"]) > 0.021 or point.y > -0.078:
            continue
        nearest_index, nearest = min(boundary_points, key=lambda item: (point.x - item[1].x) ** 2 + (point.z - item[1].z) ** 2)
        distance = math.hypot(point.x - nearest.x, point.z - nearest.z)
        if distance > 0.0090:
            continue
        weight = 1.0 - smoothstep(distance / 0.0090)
        delta_z = boundary_deltas[nearest_index] * weight
        if abs(delta_z) > 1e-8:
            deltas[index] = Vector((0.0, 0.0, delta_z))

guard_faces = (7677, 7681)
guard_vertices = {index for face_index in guard_faces for index in body.data.polygons[face_index].vertices}
for index in guard_vertices:
    deltas.pop(index, None)

inverse = body.matrix_world.inverted().to_3x3()
shape_keys = list(body.data.shape_keys.key_blocks)
for key in shape_keys:
    for index, delta in deltas.items():
        key.data[index].co += inverse @ (delta * STRENGTH)
body.data.update()

# Keep the upper lashes attached to the same reshaped lid margin.  This uses
# the identical world-space vertical correction and side-specific boundary.
lash_moves = {}
for side in ("L", "R"):
    lash = bpy.data.objects[f"Eye_{side}_UpperLashes"]
    inverse_lash = lash.matrix_world.inverted().to_3x3()
    boundary_points = [(index, world_points[index]) for index in boundaries[side]]
    moved = 0
    maximum = 0.0
    for vertex in lash.data.vertices:
        point = lash.matrix_world @ vertex.co
        nearest_index, nearest = min(
            boundary_points,
            key=lambda item: (point.x - item[1].x) ** 2 + (point.z - item[1].z) ** 2,
        )
        distance = math.hypot(point.x - nearest.x, point.z - nearest.z)
        if distance > 0.010:
            continue
        weight = 1.0 - smoothstep(distance / 0.010)
        delta = Vector((0.0, -0.00035 * weight, boundary_deltas[nearest_index] * STRENGTH * weight))
        if delta.length > 1e-8:
            vertex.co += inverse_lash @ delta
            moved += 1
            maximum = max(maximum, delta.length)
    lash.data.update()
    lash["aevrynd_revision"] = "v249r520-lid-follow-upper-lashes"
    lash_moves[lash.name] = {"verticesMoved": moved, "maximumMoveMm": maximum * 1000.0}

# The runtime scalp cap includes a thin conforming forehead/eye shell. Carry
# its eye-adjacent points with the body so the pre-existing clearance remains.
scalp = bpy.data.objects["AevryndFemaleRuntimeScalpCap_R467"]
inverse_scalp = scalp.matrix_world.inverted().to_3x3()
scalp_moved = 0
scalp_maximum = 0.0
for vertex in scalp.data.vertices:
    point = scalp.matrix_world @ vertex.co
    best = None
    for side in ("L", "R"):
        for boundary_index in boundaries[side]:
            boundary_point = world_points[boundary_index]
            distance = math.hypot(point.x - boundary_point.x, point.z - boundary_point.z)
            if best is None or distance < best[0]:
                best = (distance, boundary_index)
    distance, nearest_index = best
    if distance > 0.010:
        continue
    weight = 1.0 - smoothstep(distance / 0.010)
    delta = Vector((0.0, 0.0, boundary_deltas[nearest_index] * STRENGTH * weight))
    if delta.length > 1e-8:
        vertex.co += inverse_scalp @ delta
        scalp_moved += 1
        scalp_maximum = max(scalp_maximum, delta.length)
scalp.data.update()
scalp["aevrynd_revision"] = "v249r520-eye-shell-follow"
scalp_move = {"verticesMoved": scalp_moved, "maximumMoveMm": scalp_maximum * 1000.0}

# Preserve the complete radial iris mesh and fit it within the narrowed lids.
# Deleting radial faces creates visible white wedges. The selected local-axis
# fit preserves horizontal width while remaining overlap-free on both sides.
iris_moves = {}
for side in ("L", "R"):
    iris = bpy.data.objects[f"Eye_{side}_Iris"]
    iris.scale.x *= IRIS_SCALE[0]
    iris.scale.y *= IRIS_SCALE[1]
    iris.scale.z *= IRIS_SCALE[2]
    iris["aevrynd_revision"] = "v249r520-intact-fitted-iris"
    iris_moves[iris.name] = {"localAxisScale": list(IRIS_SCALE), "facesPreserved": len(iris.data.polygons)}

# Clip only existing optical faces that newly cross the reshaped continuous lid.
overlap_faces = {name: set() for name in OPTICAL}
overlap_before = {}
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(body, depsgraph)
    overlap_before[str(frame)] = {}
    for name in OPTICAL:
        pairs = body_tree.overlap(tree(bpy.data.objects[name], depsgraph))
        indices = {eye_face for _body_face, eye_face in pairs}
        overlap_faces[name].update(indices)
        overlap_before[str(frame)][name] = len(indices)

removed = {}
scene.frame_set(1)
for name in OPTICAL:
    obj = bpy.data.objects[name]
    obj.data = obj.data.copy()
    before = len(obj.data.polygons)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    doomed = [bm.faces[index] for index in sorted(overlap_faces[name])]
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    obj["aevrynd_revision"] = "v249r520-natural-eye-ratio-optical-clip"
    obj["aevrynd_removed_intersecting_faces"] = len(overlap_faces[name])
    removed[name] = {"beforeFaces": before, "removedFaces": len(overlap_faces[name]), "afterFaces": len(obj.data.polygons)}

scene["aevrynd_mainline_revision"] = "v249r520-natural-eye-ratio"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_CANDIDATE_AUDITS_PENDING"
body["aevrynd_eye_ratio_revision"] = "v249r520"
body["aevrynd_eye_ratio_strength"] = STRENGTH
body["aevrynd_eye_ratio_target"] = "2.23"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "strength": STRENGTH,
    "affectedVertices": len(deltas),
    "shapeKeysMovedTogether": [key.name for key in shape_keys],
    "topologyChanged": False,
    "opticalFacesRemoved": removed,
    "upperLashMoves": lash_moves,
    "scalpEyeShellMove": scalp_move,
    "intactIrisFit": iris_moves,
    "overlapFacesBeforeClip": overlap_before,
    "frames": list(FRAMES),
    "status": "AUDITS_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R520_NATURAL_EYE_RATIO=" + json.dumps(report, sort_keys=True))
