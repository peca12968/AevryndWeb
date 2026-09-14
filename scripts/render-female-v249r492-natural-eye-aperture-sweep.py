import json
import math
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-balanced-skin-r491.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-eye-aperture-r492.blend"
REPORT = ASSETS / "female-v249-mainline-natural-eye-aperture-r492.study.json"
RENDER_DIR = ASSETS / "reviews/v249r492-natural-eye-aperture-sweep"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {
    "L": {"x": 0.03452761, "z": 1.60776448, "outer_sign": 1.0},
    "R": {"x": -0.03444305, "z": 1.60776424, "outer_sign": -1.0},
}


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
    result = []
    unvisited = set(adjacency)
    while unvisited:
        start = unvisited.pop()
        component = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor not in component:
                    component.add(neighbor)
                    unvisited.discard(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, name, location, target, lens, size):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
evaluated_mesh = evaluated.to_mesh()
world_points = [evaluated.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices]
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
target_metrics = {}
for side, eye in EYES.items():
    boundary = boundaries[side]
    points = [world_points[index] for index in boundary]
    half_width = max(abs(point.x - eye["x"]) for point in points)
    for index in boundary:
        point = world_points[index]
        q = clamp((point.x - eye["x"]) / half_width, -1.0, 1.0)
        q_anatomical = q * eye["outer_sign"]
        arch = max(0.0, 1.0 - abs(q) ** 1.65)
        # The outer canthus sits slightly higher than the medial canthus.
        middle = eye["z"] + 0.00025 + 0.00030 * q_anatomical
        if point.z >= eye["z"]:
            target_z = middle + 0.00035 + 0.00445 * arch
        else:
            target_z = middle - 0.00020 - 0.00375 * arch
        canthus_fade = 1.0 - smoothstep((abs(q) - 0.78) / 0.22)
        boundary_deltas[index] = (target_z - point.z) * canthus_fade
    target_metrics[side] = {"halfWidthMm": half_width * 1000.0}

# Carry each boundary correction into the nearby continuous lid surface. This
# avoids a narrow stretched rim and keeps the existing open aperture topology.
candidate_deltas = {}
for side, eye in EYES.items():
    boundary = boundaries[side]
    boundary_points = [(index, world_points[index]) for index in boundary]
    for index, point in enumerate(world_points):
        if abs(point.x - eye["x"]) > 0.025 or abs(point.z - eye["z"]) > 0.022 or point.y > -0.078:
            continue
        nearest_index, nearest = min(
            boundary_points,
            key=lambda item: (point.x - item[1].x) ** 2 + (point.z - item[1].z) ** 2,
        )
        distance = math.hypot(point.x - nearest.x, point.z - nearest.z)
        if distance > 0.0085:
            continue
        weight = 1.0 - smoothstep(distance / 0.0085)
        outer_distance = (point.x - eye["x"]) * eye["outer_sign"]
        if point.z > eye["z"] + 0.0008 and outer_distance > 0.0064:
            weight *= 1.0 - smoothstep((outer_distance - 0.0064) / 0.0032)
        delta_z = boundary_deltas[nearest_index] * weight
        if abs(delta_z) > 1e-8:
            candidate_deltas[index] = Vector((0.0, 0.0, delta_z))

# The source mesh already has a dense n-gon transition at the right upper
# outer canthus. Preserve the two faces that form its proven non-regressing
# baseline state instead of pulling their vertices through each other.
collision_guard_faces = (7677, 7681)
collision_guard_vertices = {
    index
    for face_index in collision_guard_faces
    for index in body.data.polygons[face_index].vertices
}
for index in collision_guard_vertices:
    candidate_deltas.pop(index, None)

key_blocks = list(body.data.shape_keys.key_blocks)
original = [[point.co.copy() for point in block.data] for block in key_blocks]
inverse_vector = body.matrix_world.inverted().to_3x3()


def apply_strength(strength):
    for block_index, block in enumerate(key_blocks):
        for index, source in enumerate(original[block_index]):
            delta = candidate_deltas.get(index)
            block.data[index].co = source if delta is None else source + inverse_vector @ (delta * strength)
    body.data.update()
    scene.frame_set(1)
    bpy.context.view_layer.update()


scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera

variants = (("a-baseline-000", 0.00), ("b-open-035", 0.35), ("c-open-045", 0.45), ("d-open-055", 0.55))
for label, strength in variants:
    apply_strength(strength)
    render(scene, camera, label + "-eye-close", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700))
    render(scene, camera, label + "-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000))

selected_strength = 0.35
apply_strength(selected_strength)

# Measure the selected evaluated aperture using the same persistent indices.
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
evaluated_mesh = evaluated.to_mesh()
selected_points = [evaluated.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices]
evaluated.to_mesh_clear()
for side, boundary in boundaries.items():
    points = [selected_points[index] for index in boundary]
    width = max(point.x for point in points) - min(point.x for point in points)
    height = max(point.z for point in points) - min(point.z for point in points)
    target_metrics[side].update({"selectedWidthMm": width * 1000.0, "selectedHeightMm": height * 1000.0, "selectedAspect": width / height})

scene["aevrynd_mainline_revision"] = "v249r492-natural-eye-aperture"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "EYE_APERTURE_VISUAL_CANDIDATE_COLLISION_AUDIT_REQUIRED"
body["aevrynd_eye_aperture_revision"] = "v249r492"
body["aevrynd_eye_aperture_strength"] = selected_strength
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "continuous-body open-aperture shaping with neighborhood falloff; identical deltas applied to all six shape keys",
    "affectedVertices": len(candidate_deltas),
    "collisionGuardFaces": list(collision_guard_faces),
    "collisionGuardVertices": sorted(collision_guard_vertices),
    "maximumFullStrengthDisplacementMm": max(delta.length for delta in candidate_deltas.values()) * 1000.0,
    "variants": {label: strength for label, strength in variants},
    "selectedStrength": selected_strength,
    "selectionReason": "0.35 is the least displacement that visibly reduces the round stare while retaining a neutral open gaze; stronger bounds remain useful visual references but increase lid/globe and body self-intersection risk",
    "selectedMetrics": target_metrics,
    "visualGate": "PENDING_STRICT_REVIEW",
    "collisionGate": "PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R492_EYE_APERTURE_SWEEP=" + json.dumps(report, sort_keys=True))
