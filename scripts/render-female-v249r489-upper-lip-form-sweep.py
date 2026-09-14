import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-owned-lip-normal-r488.blend"
OUT = ASSETS / "reviews/v249r489-upper-lip-form-sweep"
REPORT = ASSETS / "female-v249-mainline-upper-lip-form-r489.study.json"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-upper-lip-form-r489.blend"
BODY = "AevryndFemaleBodyBaseV118"
UPPER_ATTR = "AevryndVermilionPlaneR484_c-defined-280"
STRENGTHS = (0.0, 0.65, 0.90, 1.15)
SELECTED_STRENGTH = 0.90


def clamp(value):
    return max(0.0, min(1.0, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def lip_top(point):
    ax = abs(point.x)
    corner = smoothstep((ax - 0.027) / 0.016)
    cupid = gaussian(ax, 0.0115, 0.0048)
    notch = gaussian(ax, 0.0, 0.0042)
    central = 1.5380 + 0.0015 * cupid - 0.00065 * notch
    return central * (1.0 - corner) + 1.5302 * corner


def delta(point, upper_weight):
    ax = abs(point.x)
    if ax >= 0.050 or point.y > -0.106 or not (1.525 < point.z < 1.548):
        return Vector()
    width = 1.0 - smoothstep((ax - 0.031) / 0.018)
    front = 1.0 - smoothstep((point.y + 0.126) / 0.020)
    gate = width * front
    if gate <= 0:
        return Vector()

    top = lip_top(point)
    cupid = gaussian(ax, 0.0115, 0.0048)
    notch = gaussian(ax, 0.0, 0.0042)
    upper = clamp(upper_weight / 0.34)

    # Give the vermilion a rounded forward plane. Keep the center restrained so
    # the paired tubercles read separately rather than as one inflated shelf.
    paired_fullness = 0.72 + 0.30 * cupid - 0.18 * notch
    outward = -0.00105 * upper * paired_fullness * gate

    # Establish the cutaneous/vermilion turn directly above the authored lip.
    top_band = gaussian(point.z, top + 0.00015, 0.00105)
    inward_groove = 0.00062 * top_band * gate

    # Shape a readable M at the upper border: paired peaks and a central notch.
    border_gate = gaussian(point.z, top, 0.00155) * gate
    vertical = (0.00055 * cupid - 0.00043 * notch) * border_gate

    # Slight lateral pull keeps the commissures from becoming rounded blobs.
    side = -1.0 if point.x < 0 else 1.0
    corner = smoothstep((ax - 0.030) / 0.015)
    lateral = -side * 0.00016 * corner * gaussian(point.z, 1.5305, 0.0020) * front
    return Vector((lateral, outward + inward_groove, vertical))


def look(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens, size):
    camera.location = location
    camera.data.lens = lens
    look(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)


def variant(strength):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    weights = [item.color[0] for item in body.data.color_attributes[UPPER_ATTR].data]
    inverse3 = body.matrix_world.inverted().to_3x3()
    deltas = {
        index: delta(point, weights[index]) * strength
        for index, point in enumerate(points)
    }
    deltas = {index: movement for index, movement in deltas.items() if movement.length > 0.000001}
    if strength:
        for key in body.data.shape_keys.key_blocks:
            for index, movement in deltas.items():
                key.data[index].co += inverse3 @ movement
        body.data.update()

    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    tag = f"s{strength:.2f}"
    views = (
        ("mouth", (0, -0.405, 1.528), (0, -0.115, 1.528), 135, (1400, 800)),
        ("oblique", (0.235, -0.405, 1.530), (0, -0.112, 1.528), 135, (1400, 800)),
        ("face", (0, -0.560, 1.585), (0, -0.060, 1.585), 108, (1100, 1100)),
    )
    for name, location, target, lens, size in views:
        render(scene, camera, f"{tag}-{name}-f01", location, target, lens, size)
    if strength == SELECTED_STRENGTH:
        scene.frame_set(1)
        scene["aevrynd_revision"] = "v249r489-upper-lip-form"
        scene["aevrynd_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_CANDIDATE_AUDITS_PENDING"
        body["aevrynd_upper_lip_form_strength"] = strength
        body["aevrynd_upper_lip_form_method"] = "continuous vermilion fullness, superior groove, cupid peaks and central notch"
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    return {
        "strength": strength,
        "verticesMoved": len(deltas) if strength else 0,
        "maximumMoveMm": max((movement.length for movement in deltas.values()), default=0.0) * 1000,
    }


OUT.mkdir(parents=True, exist_ok=True)
results = [variant(strength) for strength in STRENGTHS]
report = {
    "revision": "v249r489-study",
    "source": str(SOURCE),
    "method": "continuous-body upper vermilion fullness, superior groove, paired cupid peaks, central notch and commissure tension",
    "shapeKeysMovedTogether": 6,
    "topologyChanged": False,
    "variants": results,
    "selectedStrength": SELECTED_STRENGTH,
    "output": str(OUTPUT),
    "reviewDirectory": str(OUT),
    "status": "OFFLINE_TECHNICAL_CANDIDATE_AUDITS_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R489_UPPER_LIP_SWEEP=" + json.dumps(report, sort_keys=True))
