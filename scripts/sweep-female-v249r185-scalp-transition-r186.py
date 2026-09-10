import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-long-hair-integration-r185.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r186-scalp-transition-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-scalp-transition-r186.sweep-report.json"
SCALP = "AevryndFemaleDeformMatchedScalp_v249r163"
VARIANTS = (
    ("a-control", "control"),
    ("b-anatomical-fade", "fade"),
    ("c-soft-density", "soft"),
    ("d-hidden", "hidden"),
)


def clamp01(value):
    return max(0.0, min(1.0, value))


def smoothstep(edge0, edge1, value):
    value = clamp01((value - edge0) / (edge1 - edge0))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def modify_scalp(obj, mode):
    obj.hide_render = mode == "hidden"
    if mode in ("control", "hidden"):
        return {"verticesChanged": 0, "minimumMultiplier": 1.0, "averageMultiplier": 1.0}
    obj.data = obj.data.copy()
    density = obj.data.attributes["aevrynd_root_density"]
    multipliers = []
    changed = 0
    for vertex, item in zip(obj.data.vertices, density.data):
        x, y, z = vertex.co
        frontness = smoothstep(-0.040, -0.105, y)
        if mode == "fade":
            lateral = min(1.0, abs(x) / 0.090)
            center_peak = math.exp(-0.5 * (x / 0.027) ** 2)
            threshold = 1.666 - 0.008 * lateral + 0.010 * center_peak
            height_fade = smoothstep(threshold - 0.004, threshold + 0.020, z)
            multiplier = (1.0 - frontness) + frontness * (0.10 + 0.90 * height_fade)
        else:
            multiplier = 1.0 - 0.48 * frontness
        old = item.value
        item.value = max(0.015, old * multiplier)
        if abs(item.value - old) > 1e-7:
            changed += 1
        multipliers.append(multiplier)
    obj.data.update()
    return {
        "verticesChanged": changed,
        "minimumMultiplier": min(multipliers),
        "averageMultiplier": sum(multipliers) / len(multipliers),
    }


def render(camera, filename, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {}
for label, mode in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    metrics = modify_scalp(bpy.data.objects[SCALP], mode)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    render(camera, f"{label}-01-face-front.png", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
    render(camera, f"{label}-02-face-three-quarter.png", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
    render(camera, f"{label}-03-hair-top.png", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78)
    report[label] = {"mode": mode, **metrics}

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R186_SCALP_TRANSITION=" + json.dumps(report, sort_keys=True))
