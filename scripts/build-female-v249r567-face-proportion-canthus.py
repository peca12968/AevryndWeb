import json
import math
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-face-proportion-canthus-r567.blend"
REPORT = ASSETS / "female-v249-mainline-face-proportion-canthus-r567.build.json"
REVIEW = ASSETS / "reviews/v249r567-face-proportion-canthus"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": 0.03453, "R": -0.03444}


def gaussian(value, sigma):
    return math.exp(-0.5 * (value / sigma) ** 2)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


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
inverse3 = body.matrix_world.inverted().to_3x3()

# Selected r560 balanced lower-face field.
lower_deltas = {}
for index, point in enumerate(world_points):
    ax = abs(point.x)
    if ax > 0.110 or point.y > -0.010 or not (1.405 < point.z < 1.625):
        continue
    side = -1.0 if point.x < 0.0 else 1.0
    jaw = gaussian(ax - 0.071, 0.021) * gaussian(point.z - 1.477, 0.036) * gaussian(point.y + 0.055, 0.055)
    jaw *= 1.0 - gaussian(ax, 0.032)
    malar = gaussian(ax - 0.057, 0.018) * gaussian(point.z - 1.574, 0.022) * gaussian(point.y + 0.100, 0.028)
    chin = gaussian(ax, 0.032) * gaussian(point.z - 1.458, 0.026) * gaussian(point.y + 0.100, 0.042)
    movement = Vector((-side * 0.0030 * jaw, -0.0014 * malar, 0.0030 * chin))
    if movement.length > 0.000002:
        lower_deltas[index] = movement

# Selected r566 three-iteration outer-canthus fairing.
adjacency = defaultdict(set)
for edge in body.data.edges:
    first, second = edge.vertices
    adjacency[first].add(second)
    adjacency[second].add(first)
selected = {}
for index, point in enumerate(world_points):
    if point.y > -0.074 or not (1.600 < point.z < 1.620):
        continue
    for center_x in EYES.values():
        outward = 1.0 if center_x > 0.0 else -1.0
        outer_x = center_x + outward * 0.0104
        dx = abs(point.x - outer_x)
        dz = abs(point.z - 1.6102)
        if dx < 0.0090 and dz < 0.0100:
            weight = (1.0 - smoothstep((dx - 0.0040) / 0.0050)) * (1.0 - smoothstep((dz - 0.0050) / 0.0050))
            if weight > 0.01:
                selected[index] = weight
            break
current = [point.copy() for point in world_points]
for _ in range(3):
    previous = [point.copy() for point in current]
    for index, weight in selected.items():
        neighbors = adjacency[index]
        if not neighbors:
            continue
        average = sum((previous[neighbor] for neighbor in neighbors), Vector()) / len(neighbors)
        proposal = previous[index].lerp(average, 0.42 * weight)
        proposal.y = previous[index].y
        delta = proposal - world_points[index]
        if delta.length > 0.00135:
            proposal = world_points[index] + delta.normalized() * 0.00135
        current[index] = proposal
canthus_deltas = {index: current[index] - world_points[index] for index in selected if (current[index] - world_points[index]).length > 0.000001}

combined = dict(lower_deltas)
for index, movement in canthus_deltas.items():
    combined[index] = combined.get(index, Vector()) + movement
shape_keys = list(body.data.shape_keys.key_blocks)
for key in shape_keys:
    for index, movement in combined.items():
        key.data[index].co += inverse3 @ movement
body.data.update()
scene["aevrynd_mainline_revision"] = "v249r567-face-proportion-canthus"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_CANDIDATE_AUDITS_PENDING"
body["aevrynd_face_revision"] = "v249r567"
body["aevrynd_face_method"] = "r560 balanced jaw/malar/chin proportions plus r566 three-iteration outer-canthus fairing"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)

# Render an unobstructed review after saving the production object visibility.
for obj in bpy.data.objects:
    name = obj.name.lower()
    layer = str(obj.get("aevrynd_layer", "")).lower()
    if "hair" in name or layer.startswith("hair"):
        obj.hide_render = True
        obj.hide_viewport = True
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
REVIEW.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for label, location, target, lens in (
    ("01-front", (0.0, -0.57, 1.565), (0.0, -0.040, 1.555), 104),
    ("02-three-quarter", (0.38, -0.54, 1.575), (0.0, -0.035, 1.555), 100),
    ("03-eye-front", (0.0, -0.48, 1.608), (0.0, -0.055, 1.608), 120),
):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(REVIEW / f"{label}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "lowerFaceAffectedVertices": len(lower_deltas),
    "canthusSelectedVertices": len(selected),
    "canthusMovedVertices": len(canthus_deltas),
    "combinedAffectedVertices": len(combined),
    "maximumMoveMm": max(movement.length for movement in combined.values()) * 1000.0,
    "shapeKeysMovedTogether": [key.name for key in shape_keys],
    "topologyChanged": False,
    "runtimeDependencyAdded": False,
    "status": "AUDITS_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R567_FACE_CANDIDATE=" + json.dumps(report, sort_keys=True))
