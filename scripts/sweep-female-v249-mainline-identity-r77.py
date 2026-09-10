import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-skin-baked-r76.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-identity-r77-sweep"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (("a-control", 0.0), ("b-restrained", 0.75), ("c-balanced", 1.0), ("d-strong", 1.35))


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def sculpt(body, strength):
    moved = 0
    maximum = 0.0
    zones = {"nasal_root": 0, "bridge": 0, "alar": 0, "philtrum": 0, "chin": 0}
    for vertex in body.data.vertices:
        x, y, z = vertex.co
        ax = abs(x)
        front = gaussian(y, -0.137, 0.024)
        if front < 0.003:
            continue

        nasal_root = gaussian(x, 0.0, 0.010) * gaussian(z, 1.622, 0.018) * front
        bridge = gaussian(x, 0.0, 0.009) * gaussian(z, 1.596, 0.022) * front
        tip = gaussian(x, 0.0, 0.012) * gaussian(z, 1.568, 0.011) * front
        alar_groove = gaussian(ax, 0.029, 0.0065) * gaussian(z, 1.552, 0.012) * front
        alar_rim = gaussian(ax, 0.020, 0.008) * gaussian(z, 1.558, 0.011) * front

        # Keep the displacement above the separate upper-lip contact layer.
        upper_face_guard = 1.542 < z
        philtrum_center = gaussian(x, 0.0, 0.0042) * gaussian(z, 1.541, 0.0075) * front
        philtrum_columns = gaussian(ax, 0.0065, 0.0032) * gaussian(z, 1.542, 0.008) * front
        if not upper_face_guard:
            philtrum_center = 0.0
            philtrum_columns = 0.0

        chin = gaussian(x, 0.0, 0.027) * gaussian(z, 1.477, 0.018) * front
        chin_groove = gaussian(x, 0.0, 0.030) * gaussian(z, 1.495, 0.007) * front
        mental_side = gaussian(ax, 0.034, 0.014) * gaussian(z, 1.480, 0.020) * front

        displacement = Vector((0.0, 0.0, 0.0))
        displacement.y -= strength * (
            0.00110 * nasal_root + 0.00125 * bridge + 0.00070 * tip
        )
        displacement.y += strength * 0.00052 * alar_groove
        displacement.y -= strength * 0.00038 * alar_rim
        displacement.y += strength * 0.00038 * philtrum_center
        displacement.y -= strength * 0.00028 * philtrum_columns
        displacement.y -= strength * 0.00170 * chin
        displacement.y += strength * 0.00042 * chin_groove
        if ax > 1e-6:
            displacement.x -= math.copysign(strength * 0.00055 * mental_side, x)
        # Sub-millimetre identity asymmetry, restricted to the right nasal and
        # left chin planes, prevents a perfectly mirrored procedural result.
        displacement.y -= strength * 0.00016 * bridge * gaussian(x, 0.006, 0.008)
        displacement.y -= strength * 0.00013 * chin * gaussian(x, -0.014, 0.018)

        length = displacement.length
        if length <= 1e-7:
            continue
        vertex.co += displacement
        moved += 1
        maximum = max(maximum, length)
        if nasal_root > 0.05:
            zones["nasal_root"] += 1
        if bridge + tip > 0.05:
            zones["bridge"] += 1
        if alar_groove + alar_rim > 0.05:
            zones["alar"] += 1
        if philtrum_center + philtrum_columns > 0.05:
            zones["philtrum"] += 1
        if chin + chin_groove + mental_side > 0.05:
            zones["chin"] += 1
    body.data.update()
    return {"vertices_moved": moved, "maximum_displacement_mm": maximum * 1000.0, "zones": zones}


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {}
for name, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    for obj in bpy.data.objects:
        if is_hair(obj):
            obj.hide_render = True
    geometry = sculpt(bpy.data.objects[BODY], strength) if strength else {
        "vertices_moved": 0, "maximum_displacement_mm": 0.0, "zones": {}
    }
    camera = bpy.data.objects["Aevrynd Review Camera"]
    render(camera, f"{name}-01-front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108)
    render(camera, f"{name}-02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
    render(camera, f"{name}-03-profile", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88)
    report[name] = {"strength": strength, "geometry": geometry}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_IDENTITY_R77_SWEEP=" + json.dumps(report, sort_keys=True))
