import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-damped-outer-card-motion-r587.blend"
OUT = ASSETS / "reviews/v249r588-layered-tail-architecture-sweep"
REPORT = ASSETS / "female-v249-mainline-layered-tail-architecture-r588.study.json"
COVERAGE = "AevryndFemaleOwnedScalpGuideGroom_R587_Coverage"
CARDS = "AevryndFemaleTangentOuterHairCards_R587"
POINTS_PER_CURVE = 24
VERTICES_PER_CARD = 48
PAIR_TAIL_LIFT_MM = (42, 24, 14, 34, 20, 45, 32, 12, 54, 28, 16, 40, 50, 30, 10, 44)
VARIANTS = (
    ("a-r587-current", 1.00, 1.00, 0.00),
    ("b-soft-tail-open-locks", 0.50, 1.50, 0.50),
    ("c-layered-tail-balanced", 0.25, 1.90, 1.00),
    ("d-layered-tail-strong", 0.10, 2.30, 1.25),
)
VIEWS = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
    ("profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
    ("back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.58), 88),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def rand(index, salt=0.0):
    return (math.sin(index * 12.9898 + salt * 78.233) * 43758.5453) % 1.0


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
scene.render.resolution_x = 650
scene.render.resolution_y = 650
scene.render.resolution_percentage = 100
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
coverage = bpy.data.objects[COVERAGE]
cards = bpy.data.objects[CARDS]
radius = coverage.data.attributes["radius"].data
original_radius = [item.value for item in radius]
basis = cards.data.shape_keys.key_blocks["Basis"]
original_basis = [item.co.copy() for item in basis.data]

variant_report = {}
for label, coverage_floor, width_scale, hierarchy_scale in VARIANTS:
    for point_index, item in enumerate(radius):
        curve_index = point_index // POINTS_PER_CURVE
        local_index = point_index % POINTS_PER_CURVE
        guide_index = curve_index // 12
        t = local_index / (POINTS_PER_CURVE - 1)
        cutoff = 0.78 + 0.16 * rand(guide_index, 588.0)
        tail = smoothstep((cutoff - t) / 0.22)
        factor = coverage_floor + (1.0 - coverage_floor) * tail
        item.value = original_radius[point_index] * factor

    for card_index in range(len(original_basis) // VERTICES_PER_CARD):
        pair_index = card_index // 2
        start = card_index * VERTICES_PER_CARD
        side = -1.0 if (original_basis[start].x + original_basis[start + 1].x) < 0.0 else 1.0
        phase = (rand(pair_index, 589.0) - 0.5) * 0.8
        for point_index in range(24):
            ia = start + point_index * 2
            ib = ia + 1
            a = original_basis[ia]
            b = original_basis[ib]
            center = (a + b) * 0.5
            half = (a - b) * 0.5 * width_scale
            t = point_index / 23.0
            release = smoothstep((t - 0.34) / 0.66)
            tail = smoothstep((t - 0.58) / 0.42)
            lift = PAIR_TAIL_LIFT_MM[pair_index] * 0.001 * hierarchy_scale * tail
            sweep = math.sin(math.pi * clamp((t - 0.28) / 0.72)) * hierarchy_scale
            center += Vector((
                side * (0.0035 + 0.0030 * phase) * sweep,
                (0.0025 * phase - 0.0015) * sweep,
                lift,
            ))
            basis.data[ia].co = center + half
            basis.data[ib].co = center - half

    cards.data.update()
    bpy.context.view_layer.update()
    for view, location, target, lens in VIEWS:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(OUT / f"{label}-{view}.png")
        bpy.ops.render.render(write_still=True)
    variant_report[label] = {
        "coverageTailRadiusFloor": coverage_floor,
        "outerCardWidthScale": width_scale,
        "outerTailHierarchyScale": hierarchy_scale,
        "maximumOuterTailLiftM": max(PAIR_TAIL_LIFT_MM) * 0.001 * hierarchy_scale,
        "rootsFixedThroughFraction": 0.34,
    }

report = {
    "source": str(SOURCE),
    "method": "stagger dense-coverage tail radius by 12-child guide family, then widen and vertically layer the independent paired outer cards while preserving their roots",
    "variants": variant_report,
    "fixed": ["r587 hair colour", "r586 1.5x outer alpha", "camera", "lights", "Standard/None exposure 0"],
    "status": "VISUAL_SWEEP_PENDING_REVIEW",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R588_LAYERED_TAIL_SWEEP=" + json.dumps(report, sort_keys=True))
