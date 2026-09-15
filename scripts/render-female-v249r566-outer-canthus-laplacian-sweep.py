import json
import math
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUT = ASSETS / "reviews/v249r566-outer-canthus-laplacian-sweep"
REPORT = ASSETS / "female-v249-mainline-outer-canthus-laplacian-r566.study.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": 0.03453, "R": -0.03444}
VARIANTS = (("a-r526-control", 0), ("b-one-iteration", 1), ("c-three-iterations", 3), ("d-five-iterations", 5))


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = 1300
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
OUT.mkdir(parents=True, exist_ok=True)
for obj in bpy.data.objects:
    name = obj.name.lower()
    layer = str(obj.get("aevrynd_layer", "")).lower()
    if "hair" in name or layer.startswith("hair"):
        obj.hide_render = True
        obj.hide_viewport = True

body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
world_points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
evaluated.to_mesh_clear()
adjacency = defaultdict(set)
for edge in body.data.edges:
    first, second = edge.vertices
    adjacency[first].add(second)
    adjacency[second].add(first)

selected = {}
per_eye = {side: 0 for side in EYES}
for index, point in enumerate(world_points):
    if point.y > -0.074 or not (1.600 < point.z < 1.620):
        continue
    for side, center_x in EYES.items():
        outward = 1.0 if center_x > 0.0 else -1.0
        outer_x = center_x + outward * 0.0104
        dx = abs(point.x - outer_x)
        dz = abs(point.z - 1.6102)
        if dx >= 0.0090 or dz >= 0.0100:
            continue
        edge_fade = (1.0 - smoothstep((dx - 0.0040) / 0.0050)) * (1.0 - smoothstep((dz - 0.0050) / 0.0050))
        if edge_fade > 0.01:
            selected[index] = edge_fade
            per_eye[side] += 1
        break


def smooth_state(iterations):
    current = [point.copy() for point in world_points]
    for _ in range(iterations):
        previous = [point.copy() for point in current]
        for index, weight in selected.items():
            neighbors = adjacency[index]
            if not neighbors:
                continue
            average = sum((previous[neighbor] for neighbor in neighbors), Vector()) / len(neighbors)
            proposal = previous[index].lerp(average, 0.42 * weight)
            # Keep the fairing local and prevent depth collapse toward the eye.
            proposal.y = previous[index].y
            delta = proposal - world_points[index]
            if delta.length > 0.00135:
                proposal = world_points[index] + delta.normalized() * 0.00135
            current[index] = proposal
    return {index: current[index] - world_points[index] for index in selected if (current[index] - world_points[index]).length > 0.000001}


states = {iterations: smooth_state(iterations) for _, iterations in VARIANTS}
keys = list(body.data.shape_keys.key_blocks)
original = [[point.co.copy() for point in key.data] for key in keys]
inverse3 = body.matrix_world.inverted().to_3x3()


def apply(deltas):
    for key_index, key in enumerate(keys):
        for index, source in enumerate(original[key_index]):
            movement = deltas.get(index)
            key.data[index].co = source if movement is None else source + inverse3 @ movement
    body.data.update()


camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
camera.location = (0.0, -0.48, 1.608)
camera.data.lens = 120
look_at(camera, (0.0, -0.055, 1.608))
variant_report = {}
for label, iterations in VARIANTS:
    deltas = states[iterations]
    apply(deltas)
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)
    variant_report[label] = {
        "iterations": iterations,
        "selectedVertices": len(selected),
        "movedVertices": len(deltas),
        "maximumMoveMm": max((movement.length for movement in deltas.values()), default=0.0) * 1000.0,
    }

report = {
    "source": str(SOURCE),
    "method": "bounded X/Z Laplacian fairing on the outer-canthus neighborhood; depth is fixed, edge influence fades smoothly and total movement is clamped to 1.35mm",
    "perEyeSelectedVertices": per_eye,
    "shapeKeysMovedTogether": [key.name for key in keys],
    "variants": variant_report,
    "topologyChanged": False,
    "status": "VISUAL_CANTHUS_FAIRING_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R566_CANTHUS_LAPLACIAN=" + json.dumps(report, sort_keys=True))
