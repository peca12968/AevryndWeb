import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-eye-ratio-r520.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-commissures-r522.blend"
REPORT = ASSETS / "female-v249-mainline-natural-commissures-r522.build-report.json"
BODY = "AevryndFemaleBodyBaseV118"
STRENGTH = 1.60


def clamp(value):
    return max(0.0, min(1.0, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def delta(point):
    ax = abs(point.x)
    if ax > 0.056 or point.y > -0.104 or not (1.503 < point.z < 1.551):
        return Vector()
    front = 1.0 - smoothstep((point.y + 0.126) / 0.022)
    width = 1.0 - smoothstep((ax - 0.042) / 0.014)
    if front <= 0.0 or width <= 0.0:
        return Vector()
    slit = gaussian(point.z, 1.5293, 0.00175)
    corner = gaussian(ax, 0.0390, 0.0052)
    corner_gate = corner * slit * front
    side = -1.0 if point.x < 0.0 else 1.0
    inward_x = -side * 0.00078 * corner_gate
    recess_y = 0.00105 * corner_gate
    upper = gaussian(point.z, 1.5350, 0.0031)
    lower = gaussian(point.z, 1.5197, 0.0042)
    upper_pairs = gaussian(ax, 0.0115, 0.0060)
    center = gaussian(ax, 0.0, 0.0080)
    lip_gate = (1.0 - smoothstep((ax - 0.032) / 0.014)) * front
    volume_y = -0.00034 * upper * lip_gate * (0.72 + 0.28 * upper_pairs)
    volume_y += -0.00042 * lower * lip_gate * (0.78 + 0.22 * center)
    cupid_band = gaussian(point.z, 1.5375, 0.0017) * lip_gate
    tubercle_band = gaussian(point.z, 1.5230, 0.0022) * lip_gate
    delta_z = 0.00028 * gaussian(ax, 0.0115, 0.0048) * cupid_band
    delta_z += -0.00018 * center * gaussian(point.z, 1.5380, 0.0015) * lip_gate
    delta_z += -0.00020 * center * tubercle_band
    return Vector((inward_x, recess_y + volume_y, delta_z))


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
dg = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(dg)
mesh = evaluated.to_mesh()
points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
evaluated.to_mesh_clear()
deltas = {index: delta(point) * STRENGTH for index, point in enumerate(points)}
deltas = {index: movement for index, movement in deltas.items() if movement.length > 0.000001}
inverse = body.matrix_world.inverted().to_3x3()
keys = list(body.data.shape_keys.key_blocks)
for key in keys:
    for index, movement in deltas.items():
        key.data[index].co += inverse @ movement
body.data.update()

scene["aevrynd_mainline_revision"] = "v249r522-natural-commissures"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_CANDIDATE_AUDITS_PENDING"
body["aevrynd_perioral_revision"] = "v249r522"
body["aevrynd_perioral_strength"] = STRENGTH
body["aevrynd_perioral_method"] = "continuous commissure recess, restrained narrowing, cupid and tubercle relief"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "strength": STRENGTH,
    "affectedVertices": len(deltas),
    "maximumMoveMm": max(movement.length for movement in deltas.values()) * 1000.0,
    "shapeKeysMovedTogether": [key.name for key in keys],
    "topologyChanged": False,
    "runtimeDependencyAdded": False,
    "status": "AUDITS_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R522_NATURAL_COMMISSURES=" + json.dumps(report, sort_keys=True))
