import json
import math
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-layered-front-locks-r517.blend"
REPORT = ASSETS / "female-v249-mainline-natural-eye-ratio-r519.study.json"
RENDER_DIR = ASSETS / "reviews/v249r519-natural-eye-ratio-sweep"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {
    "L": {"x": 0.03453, "z": 1.60780, "outer_sign": 1.0},
    "R": {"x": -0.03444, "z": 1.60780, "outer_sign": -1.0},
}
VARIANTS = (("a-r517-current", 0.0), ("b-ratio-soft", 0.35), ("c-ratio-natural", 0.50), ("d-ratio-defined", 0.65))


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


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens, size):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


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

# Set a human eye target with a shallow upper arch, flatter lower lid and the
# lateral canthus slightly higher. The sweep only blends toward this target.
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

candidate_deltas = {}
for side, eye in EYES.items():
    boundary_points = [(index, world_points[index]) for index in boundaries[side]]
    for index, point in enumerate(world_points):
        if abs(point.x - eye["x"]) > 0.026 or abs(point.z - eye["z"]) > 0.021 or point.y > -0.078:
            continue
        nearest_index, nearest = min(
            boundary_points,
            key=lambda item: (point.x - item[1].x) ** 2 + (point.z - item[1].z) ** 2,
        )
        distance = math.hypot(point.x - nearest.x, point.z - nearest.z)
        if distance > 0.0090:
            continue
        weight = 1.0 - smoothstep(distance / 0.0090)
        delta_z = boundary_deltas[nearest_index] * weight
        if abs(delta_z) > 1e-8:
            candidate_deltas[index] = Vector((0.0, 0.0, delta_z))

# Preserve the known dense transition faces at the right upper outer canthus.
guard_faces = (7677, 7681)
guard_vertices = {
    index
    for face_index in guard_faces
    for index in body.data.polygons[face_index].vertices
}
for index in guard_vertices:
    candidate_deltas.pop(index, None)

keys = list(body.data.shape_keys.key_blocks)
original = [[point.co.copy() for point in key.data] for key in keys]
inverse = body.matrix_world.inverted().to_3x3()


def apply_strength(strength):
    for key_index, key in enumerate(keys):
        for index, source in enumerate(original[key_index]):
            delta = candidate_deltas.get(index)
            key.data[index].co = source if delta is None else source + inverse @ (delta * strength)
    body.data.update()
    scene.frame_set(1)
    bpy.context.view_layer.update()


def eye_metrics():
    dg = bpy.context.evaluated_depsgraph_get()
    evaluated_body = body.evaluated_get(dg)
    evaluated_mesh = evaluated_body.to_mesh()
    points = [evaluated_body.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices]
    evaluated_body.to_mesh_clear()
    result = {}
    for side, boundary in boundaries.items():
        eye_points = [points[index] for index in boundary]
        width = max(p.x for p in eye_points) - min(p.x for p in eye_points)
        height = max(p.z for p in eye_points) - min(p.z for p in eye_points)
        result[side] = {"widthMm": width * 1000.0, "heightMm": height * 1000.0, "aspect": width / height}
    return result


scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
metrics = {}
for label, strength in VARIANTS:
    apply_strength(strength)
    metrics[label] = eye_metrics()
    render(scene, camera, label + "-eye-close", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700))
    render(scene, camera, label + "-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000))
    render(scene, camera, label + "-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000))

report = {
    "source": str(SOURCE),
    "method": "continuous-body eye aperture aspect refinement with neighborhood falloff; all six shape keys move together",
    "affectedVertices": len(candidate_deltas),
    "maximumFullStrengthMoveMm": max(delta.length for delta in candidate_deltas.values()) * 1000.0,
    "variants": {label: strength for label, strength in VARIANTS},
    "metrics": metrics,
    "status": "VISUAL_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R519_NATURAL_EYE_RATIO=" + json.dumps(report, sort_keys=True))
