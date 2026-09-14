import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-eye-ratio-r520.blend"
OUT = ASSETS / "reviews/v249r521-perioral-commissure-sweep"
REPORT = ASSETS / "female-v249-mainline-perioral-commissure-r521.study.json"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (("a-r520-current", 0.0), ("b-visible-corners", 1.25), ("c-structured-corners", 1.75), ("d-strong-corners", 2.25))


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

    # Recess and slightly narrow the commissures so the lip line terminates in
    # a soft dimple instead of a long needle point.
    inward_x = -side * 0.00078 * corner_gate
    recess_y = 0.00105 * corner_gate

    # Build a shallow orbicularis roll around the corners and restore upper /
    # lower vermilion volume without inflating the whole mouth as one shelf.
    upper = gaussian(point.z, 1.5350, 0.0031)
    lower = gaussian(point.z, 1.5197, 0.0042)
    upper_pairs = gaussian(ax, 0.0115, 0.0060)
    center = gaussian(ax, 0.0, 0.0080)
    lip_gate = (1.0 - smoothstep((ax - 0.032) / 0.014)) * front
    volume_y = -0.00034 * upper * lip_gate * (0.72 + 0.28 * upper_pairs)
    volume_y += -0.00042 * lower * lip_gate * (0.78 + 0.22 * center)

    # A restrained central tubercle and paired cupid peaks break the perfectly
    # horizontal silhouette while keeping the neutral expression.
    cupid_band = gaussian(point.z, 1.5375, 0.0017) * lip_gate
    tubercle_band = gaussian(point.z, 1.5230, 0.0022) * lip_gate
    delta_z = 0.00028 * gaussian(ax, 0.0115, 0.0048) * cupid_band
    delta_z += -0.00018 * center * gaussian(point.z, 1.5380, 0.0015) * lip_gate
    delta_z += -0.00020 * center * tubercle_band

    return Vector((inward_x, recess_y + volume_y, delta_z))


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
points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
evaluated.to_mesh_clear()
full_deltas = {index: delta(point) for index, point in enumerate(points)}
full_deltas = {index: movement for index, movement in full_deltas.items() if movement.length > 0.000001}
keys = list(body.data.shape_keys.key_blocks)
original = [[point.co.copy() for point in key.data] for key in keys]
inverse = body.matrix_world.inverted().to_3x3()


def apply_strength(strength):
    for key_index, key in enumerate(keys):
        for index, source in enumerate(original[key_index]):
            movement = full_deltas.get(index)
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
        ("mouth", (0.0, -0.405, 1.528), (0.0, -0.115, 1.528), 135, (1400, 800)),
        ("oblique", (0.235, -0.405, 1.530), (0.0, -0.112, 1.528), 135, (1400, 800)),
        ("face", (0.0, -0.560, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100)),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens, size)

report = {
    "source": str(SOURCE),
    "method": "continuous-body commissure recess, subtle mouth narrowing, paired cupid peaks and central lower-lip tubercle",
    "affectedVertices": len(full_deltas),
    "maximumFullStrengthMoveMm": max(movement.length for movement in full_deltas.values()) * 1000.0,
    "shapeKeysMovedTogether": [key.name for key in keys],
    "variants": {label: strength for label, strength in VARIANTS},
    "status": "VISUAL_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R521_PERIORAL_COMMISSURE=" + json.dumps(report, sort_keys=True))
