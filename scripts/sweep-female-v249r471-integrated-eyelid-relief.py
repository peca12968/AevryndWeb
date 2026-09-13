import json
import math
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-clean-cornea-r470.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-integrated-eyelid-relief-r471.blend"
REPORT = ASSETS / "female-v249-mainline-r471.integrated-eyelid-relief-sweep.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r471-integrated-eyelid-relief-sweep"
REVIEW_DIR = ASSETS / "reviews/v249r471-integrated-eyelid-relief"
BODY = "AevryndFemaleBodyBaseV118"
EYE_CENTERS = {"L": (0.03453, 1.60780), "R": (-0.03444, 1.60780)}


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
    components, unvisited = [], set(adjacency)
    while unvisited:
        start = unvisited.pop()
        component, queue = {start}, deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor not in component:
                    component.add(neighbor)
                    unvisited.discard(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def eye_boundaries(body, evaluated_points):
    result = {}
    for side, (center_x, center_z) in EYE_CENTERS.items():
        matches = []
        for component in boundary_components(body.data):
            center = sum((evaluated_points[index] for index in component), Vector()) / len(component)
            if abs(center.x - center_x) < 0.018 and center.y < -0.075 and abs(center.z - center_z) < 0.020:
                matches.append(component)
        if len(matches) != 1:
            raise RuntimeError(f"Expected one {side} eye boundary, found {len(matches)}")
        result[side] = matches[0]
    return result


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens, size, output_dir=RENDER_DIR, frame=1):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(output_dir / f"{label}.png")
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
boundaries = eye_boundaries(body, world_points)

key_blocks = list(body.data.shape_keys.key_blocks)
original = [[point.co.copy() for point in block.data] for block in key_blocks]
inverse = body.matrix_world.inverted()
candidate_deltas = {}
for side, (center_x, center_z) in EYE_CENTERS.items():
    boundary = boundaries[side]
    boundary_points = [(index, world_points[index]) for index in boundary]
    for index, point in enumerate(world_points):
        if abs(point.x - center_x) > 0.028 or abs(point.z - center_z) > 0.024 or point.y > -0.081:
            continue
        _boundary_index, nearest = min(
            boundary_points,
            key=lambda item: (point.x - item[1].x) ** 2 + (point.z - item[1].z) ** 2,
        )
        dx, dz = point.x - nearest.x, point.z - nearest.z
        distance = math.sqrt(dx * dx + dz * dz)
        if distance > 0.0080 or point.y > nearest.y + 0.0007:
            continue
        horizontal = abs((point.x - center_x) / 0.0112)
        canthus_fade = 1.0 - smoothstep((horizontal - 0.72) / 0.28)
        if canthus_fade <= 0.0:
            continue
        upper = point.z >= center_z
        rim_width = 0.00175 if upper else 0.00155
        rim = math.exp(-0.5 * (distance / rim_width) ** 2)
        rim_amount = (0.00058 if upper else 0.00032) * rim
        crease = 0.0
        lower_roll = 0.0
        if upper and dz >= -0.0004:
            crease = 0.00025 * math.exp(-0.5 * ((distance - 0.0048) / 0.00125) ** 2)
        elif not upper and dz <= 0.0004:
            lower_roll = 0.00015 * math.exp(-0.5 * ((distance - 0.0030) / 0.00115) ** 2)
        asymmetry = 1.0 if side == "L" else 0.96
        delta_y = (-rim_amount - lower_roll + crease) * canthus_fade * asymmetry
        if abs(delta_y) > 1e-7:
            candidate_deltas[index] = Vector((0.0, delta_y, 0.0))


def apply_strength(strength):
    for block_index, block in enumerate(key_blocks):
        for index, source in enumerate(original[block_index]):
            delta_world = candidate_deltas.get(index)
            block.data[index].co = source if delta_world is None else source + inverse.to_3x3() @ (delta_world * strength)
    body.data.update()


scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for label, strength in (("a-relief-180", 1.80), ("b-relief-250", 2.50), ("c-relief-320", 3.20)):
    apply_strength(strength)
    render(scene, camera, label + "-close", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700))
    render(scene, camera, label + "-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000))

selected_strength = 1.80
apply_strength(selected_strength)
render(scene, camera, "01-eye-close-f01", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700), REVIEW_DIR)
render(scene, camera, "02-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000), REVIEW_DIR)
render(scene, camera, "03-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000), REVIEW_DIR)
render(scene, camera, "04-eye-close-f20", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700), REVIEW_DIR, frame=20)
scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r471-integrated-eyelid-relief"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "INTEGRATED_EYELID_VISUAL_CANDIDATE_COLLISION_AUDIT_REQUIRED"
body["aevrynd_eyelid_relief_revision"] = "v249r471"
body["aevrynd_eyelid_relief_strength"] = selected_strength
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "eyeBoundaryVertices": {side: len(indices) for side, indices in boundaries.items()},
    "shapeKeysMovedTogether": [block.name for block in key_blocks],
    "affectedVertices": len(candidate_deltas),
    "maximumNominalDisplacementM": max(delta.length for delta in candidate_deltas.values()),
    "variants": {"a-relief-180": 1.80, "b-relief-250": 2.50, "c-relief-320": 3.20},
    "selectedStrength": selected_strength,
    "selectionReason": "1.8 produces a readable lid margin and crease without the inflated double-ridge visible at 2.5-3.2",
    "method": "integrated upper/lower lid relief on the continuous open-eye body; identical local deltas applied to all shape keys",
    "renderDirectory": str(RENDER_DIR),
    "status": "SELECTED_VISUAL_CANDIDATE_COLLISION_AUDIT_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R471_LID_RELIEF_SWEEP=" + json.dumps(report, sort_keys=True))
