import json
import math
import os
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-commissures-r522.blend"
TARGET = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-volume-r524.blend"
REPORT = ASSETS / "female-v249-mainline-orbital-volume-r524.build.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.03453, 1.60780), "R": (-0.03444, 1.60780)}
STRENGTH = float(os.environ.get("AEVRYND_R524_STRENGTH", "2.30"))


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
for side, (center_x, center_z) in EYES.items():
    matches = []
    for component in components:
        center = sum((world_points[index] for index in component), Vector()) / len(component)
        if abs(center.x - center_x) < 0.018 and center.y < -0.075 and abs(center.z - center_z) < 0.020:
            matches.append(component)
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {side} eye boundary, found {len(matches)}")
    boundaries[side] = matches[0]

deltas = {}
for side, (center_x, center_z) in EYES.items():
    boundary_points = [world_points[index] for index in boundaries[side]]
    for index, point in enumerate(world_points):
        dx = point.x - center_x
        dz = point.z - center_z
        if abs(dx) > 0.031 or not (-0.026 < dz < 0.025) or point.y > -0.076:
            continue
        nearest = min(math.hypot(point.x - edge.x, point.z - edge.z) for edge in boundary_points)
        # Keep the r520 aperture and its attachment ring exact.
        if nearest < 0.0022:
            continue
        horizontal = gaussian(dx, 0.0, 0.0145)
        lateral_fade = gaussian(dx, 0.0, 0.022)
        upper_roll = gaussian(dz, 0.0068, 0.0023) * horizontal
        upper_crease = gaussian(dz, 0.0114, 0.0019) * horizontal
        brow_transition = gaussian(dz, 0.0170, 0.0045) * lateral_fade
        lower_roll = gaussian(dz, -0.0062, 0.0024) * horizontal
        tear_trough = gaussian(dz, -0.0132, 0.0028) * gaussian(
            dx, -0.003 if side == "L" else 0.003, 0.013
        )
        malar = gaussian(dz, -0.0200, 0.0048) * gaussian(dx, 0.0, 0.018)
        # The r523 signed-recess study proved that pushing the crease and tear
        # trough inward enters the cornea/sclera envelope and makes the eyes
        # read darker. Build the crease by letting the outward roll return to
        # the unchanged surface instead of cutting into the eyeball volume.
        delta_y = -0.00034 * upper_roll
        delta_y += -0.00014 * brow_transition
        delta_y += -0.00026 * lower_roll
        delta_y += -0.00017 * malar
        if abs(delta_y) > 1e-7:
            deltas[index] = Vector((0.0, delta_y, 0.0))

shape_keys = list(body.data.shape_keys.key_blocks)
inverse = body.matrix_world.inverted().to_3x3()
for key in shape_keys:
    for index, movement in deltas.items():
        key.data[index].co += inverse @ (movement * STRENGTH)
body.data.update()

scene["aevrynd_character_revision"] = "v249r524-orbital-volume"
scene["aevrynd_character_status"] = "offline technical candidate; audits pending"
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET), check_existing=False)

report = {
    "source": str(SOURCE),
    "target": str(TARGET),
    "method": "aperture-preserving outward upper/lower eyelid rolls with collision-safe return to the unchanged crease and tear-trough surface",
    "selectedSweepVariant": "c-structured-relief",
    "strength": STRENGTH,
    "boundaryClearanceMm": 2.2,
    "affectedVertices": len(deltas),
    "maximumDisplacementMm": max(movement.length for movement in deltas.values()) * STRENGTH * 1000.0,
    "shapeKeysMovedTogether": [key.name for key in shape_keys],
    "status": "BUILT_AUDITS_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R524_BUILD=" + json.dumps(report, sort_keys=True))
