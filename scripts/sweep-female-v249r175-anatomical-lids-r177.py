import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cornea-response-r175.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r177-anatomical-lids-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-anatomical-lids-r177.sweep-report.json"
OUT.mkdir(parents=True, exist_ok=True)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def apply_lids(body, original, normals, factor):
    moved = 0
    maximum = 0.0
    for vertex, base, normal in zip(body.data.vertices, original, normals):
        vertex.co = base
        p = base
        if p.y > -0.096 or not (1.580 < p.z < 1.632):
            continue
        delta = Vector((0.0, 0.0, 0.0))
        for cx in (-0.035, 0.035):
            u = (p.x - cx) / 0.034
            if abs(u) >= 1.12:
                continue
            horizontal = max(0.0, 1.0 - (u / 1.12) ** 2) ** 1.65
            front = gaussian(p.y, -0.126, 0.022)
            arch = max(0.0, 1.0 - u * u)
            upper_center = 1.6078 + 0.0042 * arch
            lower_center = 1.5994 - 0.0015 * arch
            crease_center = upper_center + 0.0084
            upper = horizontal * front * gaussian(p.z, upper_center, 0.0025)
            lower = horizontal * front * gaussian(p.z, lower_center, 0.0027)
            crease = horizontal * front * gaussian(p.z, crease_center, 0.0026)
            trough = horizontal * front * gaussian(p.z, lower_center - 0.0085, 0.0035)

            # Positive normal builds the lid roll; negative normal separates the
            # crease/trough plane. Both remain sub-millimetre at factor 1.
            delta += normal * factor * (0.00058 * upper + 0.00034 * lower - 0.00050 * crease - 0.00016 * trough)

            # Move both lid margins together to form a subtle upward outer
            # canthus without changing the eye centre or mirroring incorrectly.
            outer_axis = u * (1.0 if cx > 0.0 else -1.0)
            tilt = 0.00052 * outer_axis * horizontal * front
            delta.z += factor * tilt * (upper + lower)

            # A small central upper-lid drop increases globe coverage and makes
            # the upper margin less mechanically circular.
            delta.z -= factor * 0.00018 * upper * arch
        if delta.length > 1e-7:
            vertex.co += delta
            moved += 1
            maximum = max(maximum, delta.length)
    body.data.update()
    return {"verticesMoved": moved, "maxMoveMm": maximum * 1000.0}


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
body.data = body.data.copy()
original = [vertex.co.copy() for vertex in body.data.vertices]
body.data.update()
normals = [vertex.normal.copy() for vertex in body.data.vertices]

for obj in bpy.data.objects:
    layer = str(obj.get("aevrynd_layer", ""))
    if obj.type == "CURVES" or "hair" in layer.lower() or "scalp" in obj.name.lower():
        obj.hide_render = True

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("eye", (0.0, -0.47, 1.610), (0.0, -0.065, 1.608), 112),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
)
variants = (("00-control", 0.0), ("01-soft", 0.72), ("02-balanced", 1.0), ("03-strong", 1.28))
results = []
for name, factor in variants:
    metrics = apply_lids(body, original, normals, factor)
    for view, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(OUT / f"{name}-{view}.png")
        bpy.ops.render.render(write_still=True)
    results.append({"name": name, "factor": factor, **metrics})

report = {"source": str(SOURCE), "variants": results, "hairHiddenForDiagnostic": True, "status": "STRICT_VISUAL_REVIEW_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R177_ANATOMICAL_LIDS_SWEEP=" + json.dumps(report, sort_keys=True))
