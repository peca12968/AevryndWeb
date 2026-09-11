import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-matte-root-underlayer-r287.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-asymmetric-silhouette-r290.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-asymmetric-silhouette-r290.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r290-asymmetric-silhouette"
CARDS = "AevryndFemaleRuntimeHairCards_R276"
SOURCE_MATERIAL = "Aevrynd_RuntimeHairCards_DenseAlpha_R276"
MATERIAL = "Aevrynd_RuntimeHairCards_Asymmetric_R290"
POINTS = 24
STRIDE = POINTS * 2
CARD_COUNT = 384


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def reshape(cards):
    mesh = cards.data
    rng = random.Random(2900384)
    stats = {"back": 0, "front": 0, "side": 0, "maxCenterShiftM": 0.0, "maxTipLiftM": 0.0}
    for card_index in range(CARD_COUNT):
        base = card_index * STRIDE
        centers = []
        halves = []
        for point_index in range(POINTS):
            left = mesh.vertices[base + point_index * 2].co.copy()
            right = mesh.vertices[base + point_index * 2 + 1].co.copy()
            centers.append((left + right) * 0.5)
            halves.append((right - left) * 0.5)
        root = centers[0]
        middle = centers[12]
        is_back = root.y > 0.005
        is_side = abs(middle.x) > 0.082
        category = "back" if is_back else ("side" if is_side else "front")
        stats[category] += 1
        phase = rng.uniform(-math.pi, math.pi)
        bend = rng.uniform(-0.0038, 0.0038)
        # Deliberately different left/right silhouettes: the left carries a
        # broader S bend, while the right tucks inward before opening at tips.
        handed = -1.0 if middle.x < 0.0 else 1.0
        outer_gain = rng.uniform(0.004, 0.010) if is_side else rng.uniform(0.001, 0.004)
        tip_lift = rng.uniform(0.002, 0.026)
        if card_index % 11 in (0, 1):
            tip_lift *= 0.28
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            original_center = centers[point_index]
            half = halves[point_index]
            radial = Vector((original_center.x, original_center.y + 0.010, 0.0))
            if radial.length < 1e-6:
                radial = Vector((1.0, 0.0, 0.0))
            radial.normalize()
            circumferential = Vector((radial.y, -radial.x, 0.0))
            envelope = math.sin(math.pi * t) ** 2
            outward = radial * ((0.0025 + (0.0048 if is_back else 0.0036)) * envelope)
            irregular = circumferential * bend * envelope * math.sin(math.pi * t + phase)
            side_arc = Vector((handed, 0.0, 0.0)) * outer_gain * smoothstep((t - 0.20) / 0.62) * (1.0 - 0.25 * smoothstep((t - 0.88) / 0.12))
            # Uneven, upward tip retreat breaks the ruler-straight hem and also
            # moves ends away from shoulders rather than toward the body.
            lift = Vector((0.0, 0.0, tip_lift * smoothstep((t - 0.76) / 0.24)))
            center = original_center + outward + irregular + side_arc + lift
            stats["maxCenterShiftM"] = max(stats["maxCenterShiftM"], (center - original_center).length)
            stats["maxTipLiftM"] = max(stats["maxTipLiftM"], lift.z)
            if point_index <= 4:
                width_scale = 1.0
            else:
                target_scale = 0.48 if is_back else (0.64 if is_side else 0.72)
                width_scale = 1.0 + (target_scale - 1.0) * smoothstep((t - 0.17) / 0.34)
            mesh.vertices[base + point_index * 2].co = center - half * width_scale
            mesh.vertices[base + point_index * 2 + 1].co = center + half * width_scale
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    mesh.update()
    return stats


def tune_material(cards):
    material = bpy.data.materials[SOURCE_MATERIAL].copy()
    material.name = MATERIAL
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Roughness"].default_value = 0.56
    shader.inputs["Specular IOR Level"].default_value = 0.10
    anisotropic = shader.inputs.get("Anisotropic IOR Level")
    if anisotropic:
        anisotropic.default_value = 0.68
    opacity = next(node for node in material.node_tree.nodes if node.type == "MATH" and node.operation == "MULTIPLY")
    opacity.inputs[1].default_value = 1.48
    opacity.label = "Separated clump coverage 1.48x"
    material["aevrynd_revision"] = "v249r290"
    material["aevrynd_alpha_gain"] = 1.48
    cards.data.materials.clear()
    cards.data.materials.append(material)
    return material


def render(camera, frame, name, location):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, (0.0, 0.0, 1.56))
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
cards = bpy.data.objects[CARDS]
if len(cards.data.vertices) != CARD_COUNT * STRIDE:
    raise RuntimeError("unexpected r287 card topology")
stats = reshape(cards)
material = tune_material(cards)
cards["aevrynd_revision"] = "v249r290"
cards["aevrynd_visual_change"] = "narrowed back cards; outward volume; asymmetric side arcs; uneven tips"
scene["aevrynd_mainline_revision"] = "v249r290-asymmetric-silhouette"
scene["aevrynd_hair_layers"] = "scalp_underlayer|runtime_dynamic_cards.asymmetric|hairline_transition.head_bound|flyaways"
scene["aevrynd_release_state"] = "ASYMMETRIC_SILHOUETTE_COLLISION_AND_VISUAL_REVIEW_PENDING"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in (
    (1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)),
    (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)),
    (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59)),
):
    render(camera, frame, name, location)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "cardObject": CARDS,
    "cardCount": CARD_COUNT, "material": material.name, "alphaGain": 1.48,
    "reshape": stats, "smoothPolygons": sum(p.use_smooth for p in cards.data.polygons),
    "topologyChanged": False, "weightsChanged": False, "animationChanged": False,
    "collisionAuditRequired": True, "ownedAssetOnly": True,
    "renderDirectory": str(RENDER_DIR), "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R290_ASYMMETRIC_SILHOUETTE=" + json.dumps(report, sort_keys=True))
