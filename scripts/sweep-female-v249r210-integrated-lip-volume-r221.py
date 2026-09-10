import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r221-integrated-lip-volume-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-integrated-lip-volume-r221.sweep-report.json"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (("a-control", 0.0), ("b-subtle", 0.55), ("c-balanced", 0.85), ("d-strong", 1.15))


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def consolidate(body, name):
    key = body.shape_key_add(name=name, from_mix=True)
    previous = [old.name for old in body.data.shape_keys.key_blocks[1:-1]]
    for old in body.data.shape_keys.key_blocks[1:-1]:
        old.value = 0.0
    key.value = 1.0
    return key, previous


def sculpt(body, strength):
    key, previous = consolidate(body, f"Aevrynd_IntegratedLipVolume_R221_{strength:.2f}")
    counts = {"upper_vermilion": 0, "central_tubercle": 0, "cupid_peaks": 0, "center_notch": 0, "commissure_blend": 0}
    maxima = {name: 0.0 for name in counts}
    moved = 0
    maximum = 0.0
    for point in key.data:
        p = point.co.copy()
        ax = abs(p.x)
        if ax > 0.052 or p.y > -0.108 or not (1.518 < p.z < 1.544):
            continue
        delta = Vector()

        upper = gaussian(ax, 0.0, 0.038) * gaussian(p.z, 1.5328, 0.0068) * gaussian(p.y, -0.129, 0.016)
        if upper > 0.035:
            component = Vector((0.0, -0.00155 * strength * upper, 0.0))
            delta += component
            counts["upper_vermilion"] += 1
            maxima["upper_vermilion"] = max(maxima["upper_vermilion"], component.length)

        tubercle = upper * gaussian(ax, 0.0, 0.0105) * gaussian(p.z, 1.5300, 0.0045)
        if tubercle > 0.030:
            component = Vector((0.0, -0.00058 * strength * tubercle, 0.00008 * strength * tubercle))
            delta += component
            counts["central_tubercle"] += 1
            maxima["central_tubercle"] = max(maxima["central_tubercle"], component.length)

        peaks = upper * gaussian(ax, 0.0105, 0.0058) * gaussian(p.z, 1.5370, 0.0042)
        if peaks > 0.025:
            component = Vector((0.0, -0.00024 * strength * peaks, 0.00064 * strength * peaks))
            delta += component
            counts["cupid_peaks"] += 1
            maxima["cupid_peaks"] = max(maxima["cupid_peaks"], component.length)

        notch = upper * gaussian(ax, 0.0, 0.0048) * gaussian(p.z, 1.5385, 0.0038)
        if notch > 0.022:
            component = Vector((0.0, 0.00010 * strength * notch, -0.00038 * strength * notch))
            delta += component
            counts["center_notch"] += 1
            maxima["center_notch"] = max(maxima["center_notch"], component.length)

        corner = gaussian(ax, 0.0385, 0.0085) * gaussian(p.z, 1.5285, 0.0075) * gaussian(p.y, -0.116, 0.024)
        if corner > 0.045:
            side = -1.0 if p.x < 0.0 else 1.0
            component = Vector((-side * 0.00010 * strength * corner, -0.00022 * strength * corner, 0.00004 * strength * corner))
            delta += component
            counts["commissure_blend"] += 1
            maxima["commissure_blend"] = max(maxima["commissure_blend"], component.length)

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


def render(camera, filename, location, target, lens, size):
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
        ("01-face-front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100)),
        ("02-mouth-close", (0.0, -0.43, 1.525), (0.0, -0.105, 1.525), 120, (1100, 760)),
        ("03-three-quarter", (0.45, -0.62, 1.58), (0.0, -0.015, 1.565), 92, (1000, 1000)),
        ("04-profile", (0.70, -0.03, 1.57), (0.0, -0.010, 1.555), 96, (1000, 1000)),
    )
    for view_name, location, target, lens, size in views:
        render(camera, f"{label}-{view_name}.png", location, target, lens, size)
    report["variants"][label] = metrics
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R221_INTEGRATED_LIP_SWEEP=" + json.dumps(report, sort_keys=True))
