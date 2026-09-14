import json
import math
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-commissures-r522.blend"
OUT = ASSETS / "reviews/v249r523-orbital-volume-sweep"
REPORT = ASSETS / "female-v249-mainline-orbital-volume-r523.study.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.03453, 1.60780), "R": (-0.03444, 1.60780)}
VARIANTS = (("a-r522-current", 0.0), ("b-visible-relief", 1.80), ("c-structured-relief", 2.30), ("d-strong-relief", 2.80))


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


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
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
dg = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(dg)
mesh = evaluated.to_mesh()
world_points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
evaluated.to_mesh_clear()

components = boundary_components(body.data)
boundaries = {}
for side, (cx, cz) in EYES.items():
    matches = []
    for component in components:
        center = sum((world_points[index] for index in component), Vector()) / len(component)
        if abs(center.x - cx) < 0.018 and center.y < -0.075 and abs(center.z - cz) < 0.020:
            matches.append(component)
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {side} eye boundary, found {len(matches)}")
    boundaries[side] = matches[0]

deltas = {}
for side, (cx, cz) in EYES.items():
    boundary_points = [world_points[index] for index in boundaries[side]]
    for index, point in enumerate(world_points):
        dx = point.x - cx
        dz = point.z - cz
        if abs(dx) > 0.031 or not (-0.026 < dz < 0.025) or point.y > -0.076:
            continue
        nearest = min(math.hypot(point.x - edge.x, point.z - edge.z) for edge in boundary_points)
        # Preserve the proven r520 aperture and its immediate attachment ring.
        if nearest < 0.0022:
            continue
        horizontal = gaussian(dx, 0.0, 0.0145)
        lateral_fade = gaussian(dx, 0.0, 0.022)
        upper_roll = gaussian(dz, 0.0068, 0.0023) * horizontal
        upper_crease = gaussian(dz, 0.0114, 0.0019) * horizontal
        brow_transition = gaussian(dz, 0.0170, 0.0045) * lateral_fade
        lower_roll = gaussian(dz, -0.0062, 0.0024) * horizontal
        tear_trough = gaussian(dz, -0.0132, 0.0028) * gaussian(dx, -0.003 if side == "L" else 0.003, 0.013)
        malar = gaussian(dz, -0.0200, 0.0048) * gaussian(dx, 0.0, 0.018)

        # Negative Y is outward toward the camera. Alternate shallow rolls and
        # recesses to create anatomical transitions instead of a raised ring.
        delta_y = -0.00034 * upper_roll + 0.00046 * upper_crease
        delta_y += -0.00014 * brow_transition
        delta_y += -0.00026 * lower_roll + 0.00034 * tear_trough
        delta_y += -0.00017 * malar
        if abs(delta_y) > 1e-7:
            deltas[index] = Vector((0.0, delta_y, 0.0))

keys = list(body.data.shape_keys.key_blocks)
original = [[point.co.copy() for point in key.data] for key in keys]
inverse = body.matrix_world.inverted().to_3x3()


def apply_strength(strength):
    for key_index, key in enumerate(keys):
        for index, source in enumerate(original[key_index]):
            movement = deltas.get(index)
            key.data[index].co = source if movement is None else source + inverse @ (movement * strength)
    body.data.update()


scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for label, strength in VARIANTS:
    apply_strength(strength)
    for view, location, target, lens, size in (
        ("eye-close", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
        ("front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100)),
        ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000)),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens, size)

report = {
    "source": str(SOURCE),
    "method": "aperture-preserving upper-lid roll/crease, lower-lid roll, tear-trough and malar transition",
    "boundaryClearanceMm": 2.2,
    "affectedVertices": len(deltas),
    "maximumFullStrengthMoveMm": max(movement.length for movement in deltas.values()) * 1000.0,
    "shapeKeysMovedTogether": [key.name for key in keys],
    "variants": {label: strength for label, strength in VARIANTS},
    "status": "VISUAL_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R523_ORBITAL_VOLUME=" + json.dumps(report, sort_keys=True))
