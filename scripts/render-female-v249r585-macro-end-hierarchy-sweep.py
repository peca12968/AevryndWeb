import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-balanced-collision-safe-hair-r584.blend"
OUT = ASSETS / "reviews/v249r585-macro-end-hierarchy-sweep"
REPORT = ASSETS / "female-v249-mainline-macro-end-hierarchy-r585.study.json"
COVERAGE = "AevryndFemaleOwnedScalpGuideGroom_R584_Coverage"
POINTS = 24
CHILDREN_PER_GUIDE = 12
VARIANTS = (
    ("a-r584-current", 0.000),
    ("b-end-hierarchy-10mm", 0.010),
    ("c-end-hierarchy-20mm", 0.020),
    ("d-end-hierarchy-30mm", 0.030),
    ("e-end-hierarchy-40mm", 0.040),
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


def render(scene, camera, label, location, target, lens):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)


def apply_hierarchy(data, base_positions, strength):
    data.points.foreach_set("position", [axis for point in base_positions for axis in point])
    moved = 0
    maximum = 0.0
    family_values = {}
    for curve_index, curve in enumerate(data.curves):
        guide_index = curve_index // CHILDREN_PER_GUIDE
        family = guide_index // 7
        if family not in family_values:
            raw = rand(family, 101.0)
            family_values[family] = max(0.0, (raw - 0.22) / 0.78)
        hierarchy = family_values[family]
        child_variation = (rand(curve_index, 102.0) - 0.5) * strength * 0.12
        lift = max(0.0, strength * hierarchy + child_variation)
        root = base_positions[curve.first_point_index]
        side = -1.0 if root.x < 0.0 else 1.0
        lateral = side * strength * (rand(family, 103.0) - 0.35) * 0.16
        depth = strength * (rand(family, 104.0) - 0.5) * 0.10
        for local_index in range(curve.points_length):
            point_index = curve.first_point_index + local_index
            t = local_index / max(1, curve.points_length - 1)
            envelope = smoothstep((t - 0.58) / 0.42)
            if envelope <= 0.0:
                continue
            point = base_positions[point_index].copy()
            point.z += lift * envelope
            point.x += lateral * envelope
            point.y += depth * envelope
            data.points[point_index].position = point
            displacement = (point - base_positions[point_index]).length
            maximum = max(maximum, displacement)
            moved += 1
    return {"movedPoints": moved, "maximumDisplacementM": maximum, "families": len(family_values)}


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
coverage = bpy.data.objects[COVERAGE]
base_positions = [point.position.copy() for point in coverage.data.points]
variant_report = {}
for label, strength in VARIANTS:
    stats = apply_hierarchy(coverage.data, base_positions, strength)
    bpy.context.view_layer.update()
    for view, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        ("profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
        ("back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.58), 88),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens)
    variant_report[label] = {"strengthM": strength, **stats}

report = {
    "source": str(SOURCE),
    "method": "group each 12-child root family into coarse seven-guide macro regions; keep roots and upper 58% fixed, then apply deterministic family-level upward end hierarchy with restrained lateral/depth offsets",
    "variants": variant_report,
    "fixed": ["r584 direct warm tone", "r584 scalp/outer-card geometry", "review lights", "Standard/None exposure 0"],
    "status": "VISUAL_SWEEP_PENDING_REVIEW",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R585_MACRO_END_HIERARCHY=" + json.dumps(report, sort_keys=True))
