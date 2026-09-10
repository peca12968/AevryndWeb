import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r217-nasal-perioral-planes-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-nasal-perioral-planes-r217.sweep-report.json"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (("a-control", 0.0), ("b-subtle", 0.75), ("c-balanced", 1.15), ("d-strong", 1.55))


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def consolidate(body):
    key = body.shape_key_add(name="Aevrynd_NasalPerioralPlanes_R217", from_mix=True)
    previous = [old.name for old in body.data.shape_keys.key_blocks[1:-1]]
    for old in body.data.shape_keys.key_blocks[1:-1]:
        old.value = 0.0
    key.value = 1.0
    return key, previous


def sculpt(body, strength):
    key, previous = consolidate(body)
    names = (
        "alar_groove", "alar_rim", "nasal_tip", "columella", "nasolabial",
        "mouth_corner", "lateral_lip_mound", "mental_sulcus", "chin_pad",
    )
    counts = {name: 0 for name in names}
    maxima = {name: 0.0 for name in names}
    moved = 0
    maximum = 0.0
    for point in key.data:
        p = point.co.copy()
        ax = abs(p.x)
        side = -1.0 if p.x < 0.0 else 1.0
        front = gaussian(p.y, -0.120, 0.030)
        delta = Vector()

        fields = {}
        fields["alar_groove"] = Vector((side * 0.00010, 0.00078, 0.0)) * (
            gaussian(ax, 0.032, 0.0060) * gaussian(p.z, 1.554, 0.014) * front
        )
        fields["alar_rim"] = Vector((side * 0.00030, -0.00058, 0.00014)) * (
            gaussian(ax, 0.023, 0.0080) * gaussian(p.z, 1.547, 0.010) * gaussian(p.y, -0.127, 0.019)
        )
        fields["nasal_tip"] = Vector((0.0, -0.00042, 0.00016)) * (
            gaussian(ax, 0.0, 0.013) * gaussian(p.z, 1.562, 0.012) * gaussian(p.y, -0.137, 0.015)
        )
        fields["columella"] = Vector((0.0, -0.00048, -0.00025)) * (
            gaussian(ax, 0.0, 0.010) * gaussian(p.z, 1.541, 0.010) * gaussian(p.y, -0.124, 0.020)
        )
        z_fraction = max(0.0, min(1.0, (1.538 - p.z) / 0.045))
        fold_x = 0.032 + 0.014 * z_fraction
        fields["nasolabial"] = Vector((0.0, 0.00043, 0.0)) * (
            gaussian(ax, fold_x, 0.0062) * gaussian(p.z, 1.518, 0.026) * gaussian(p.y, -0.103, 0.033)
        )
        fields["mouth_corner"] = Vector((side * 0.00014, 0.00052, (0.00010 if p.x < 0.0 else -0.00006))) * (
            gaussian(ax, 0.039, 0.0065) * gaussian(p.z, 1.497, 0.010) * gaussian(p.y, -0.105, 0.030)
        )
        fields["lateral_lip_mound"] = Vector((0.0, -0.00030, 0.0)) * (
            gaussian(ax, 0.027, 0.009) * gaussian(p.z, 1.505, 0.012) * gaussian(p.y, -0.124, 0.022)
        )
        fields["mental_sulcus"] = Vector((0.0, 0.00066, -0.00006)) * (
            gaussian(ax, 0.0, 0.030) * gaussian(p.z, 1.476, 0.010) * gaussian(p.y, -0.105, 0.030)
        )
        fields["chin_pad"] = Vector((-side * 0.00012, -0.00072, 0.00008)) * (
            gaussian(ax, 0.017, 0.025) * gaussian(p.z, 1.455, 0.018) * gaussian(p.y, -0.082, 0.040)
        )

        for name, component in fields.items():
            component *= strength
            if component.length <= 0.000025:
                continue
            delta += component
            counts[name] += 1
            maxima[name] = max(maxima[name], component.length)
        if delta.length > 0.000001:
            point.co += delta
            moved += 1
            maximum = max(maximum, delta.length)
    body.data.update()
    return {
        "shapeKey": key.name,
        "consolidatedShapeKeys": previous,
        "verticesMoved": moved,
        "maximumDeltaMm": maximum * 1000.0,
        "regions": counts,
        "componentMaxMm": {name: value * 1000.0 for name, value in maxima.items()},
    }


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens, size=(1000, 1000)):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": {}, "status": "VISUAL_SELECTION_PENDING"}
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    metrics = {"strength": strength}
    if strength:
        metrics.update(sculpt(bpy.data.objects[BODY], strength))
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.585), 88),
        ("02-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.585), 88),
        ("03-face-profile", (0.70, -0.03, 1.60), (0.0, -0.010, 1.570), 92),
        ("04-nose-mouth-close", (0.0, -0.45, 1.545), (0.0, -0.055, 1.525), 105),
    )
    for view_name, location, target, lens in views:
        render(camera, f"{label}-{view_name}.png", location, target, lens)
    report["variants"][label] = metrics
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R217_NASAL_PERIORAL_SWEEP=" + json.dumps(report, sort_keys=True))
