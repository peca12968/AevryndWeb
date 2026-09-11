import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r302-eyelid-aperture-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eyelid-aperture-r302.study.json"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
VARIANTS = (
    ("a-current", 0.0, 0.00525),
    ("b-soft", 0.72, 0.00355),
    ("c-natural", 0.86, 0.00315),
    ("d-covered", 1.0, 0.00275),
    ("e-adult", 1.0, 0.00185),
    ("f-heavy", 1.0, 0.00110),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def apply_aperture(body, strength, upper_height):
    selected = {side: {"upper": 0, "lower": 0} for side in EYES}
    for side, (cx, cz, anatomical_sign) in EYES.items():
        for vertex in body.data.vertices:
            point = vertex.co
            u = (point.x - cx) / 0.01025
            if abs(u) >= 1.08 or point.y > -0.132:
                continue
            edge = math.sqrt(max(0.0, 1.0 - min(1.0, u * u)))
            old_upper = cz + 0.00525 * edge
            old_lower = cz - 0.00448 * edge
            outer = anatomical_sign * u
            if abs(point.z - old_upper) < 0.00165:
                target = cz + upper_height * edge - 0.00032 * outer * edge
                falloff = max(0.0, 1.0 - abs(point.z - old_upper) / 0.00165)
                point.z += (target - point.z) * strength * falloff
                point.y -= 0.00018 * strength * falloff
                selected[side]["upper"] += 1
            elif abs(point.z - old_lower) < 0.00145:
                target = cz - 0.00395 * edge - 0.00010 * outer * edge
                falloff = max(0.0, 1.0 - abs(point.z - old_lower) / 0.00145)
                point.z += (target - point.z) * min(strength, 0.78) * falloff
                point.y -= 0.00008 * strength * falloff
                selected[side]["lower"] += 1
    body.data.update()
    return selected


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
body = bpy.data.objects[BODY]
body.data = body.data.copy()
original = [vertex.co.copy() for vertex in body.data.vertices]
metrics = {}
for name, strength, height in VARIANTS:
    for vertex, coordinate in zip(body.data.vertices, original):
        vertex.co = coordinate
    body.data.update()
    selected = apply_aperture(body, strength, height) if strength else {side: {"upper": 0, "lower": 0} for side in EYES}
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = (0.0, -0.68, 1.605)
    camera.data.lens = 92
    look_at(camera, (0.0, -0.035, 1.606))
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.filepath = str(OUT / f"{name}-face-close.png")
    bpy.ops.render.render(write_still=True)
    camera.location = (0.45, -0.62, 1.62)
    camera.data.lens = 90
    look_at(camera, (0.0, -0.02, 1.605))
    scene.render.filepath = str(OUT / f"{name}-three-quarter.png")
    bpy.ops.render.render(write_still=True)
    metrics[name] = {"strength": strength, "upperHeightM": height, "selectedVertices": selected}

report = {
    "source": str(SOURCE),
    "renderDirectory": str(OUT),
    "variants": metrics,
    "status": "STRICT_VISUAL_SELECTION_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R302_EYELID_SWEEP=" + json.dumps(report, sort_keys=True))
