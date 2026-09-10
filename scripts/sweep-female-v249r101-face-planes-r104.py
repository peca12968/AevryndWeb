import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-scalp-foundation-r101.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r101-face-planes-r104-sweep"
BODY = "AevryndFemaleBodyBaseV118"


def gaussian(value, center, spread):
    return math.exp(-0.5 * ((value - center) / spread) ** 2)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def sculpt(body, original, scale):
    moved = 0
    maximum = 0.0
    zones = {"jaw": 0, "malar": 0, "buccal": 0, "chin": 0, "nose": 0}
    for vertex, source in zip(body.data.vertices, original):
        x, y, z = source
        ax = abs(x)
        if ax > 0.115 or not (1.425 < z < 1.655):
            vertex.co = source
            continue

        jaw = (
            gaussian(ax, 0.076, 0.025) * gaussian(z, 1.486, 0.043)
            * gaussian(y, -0.025, 0.065) * (1.0 - gaussian(ax, 0.0, 0.030))
        )
        malar = gaussian(ax, 0.057, 0.019) * gaussian(z, 1.568, 0.025) * gaussian(y, -0.104, 0.033)
        buccal = gaussian(ax, 0.061, 0.020) * gaussian(z, 1.526, 0.027) * gaussian(y, -0.105, 0.034)
        chin = gaussian(ax, 0.018, 0.028) * gaussian(z, 1.467, 0.024) * gaussian(y, -0.122, 0.040)
        bridge = gaussian(ax, 0.0, 0.012) * gaussian(z, 1.602, 0.029) * gaussian(y, -0.142, 0.038)
        tip = gaussian(ax, 0.0, 0.014) * gaussian(z, 1.558, 0.014) * gaussian(y, -0.164, 0.030)
        alar = gaussian(ax, 0.024, 0.011) * gaussian(z, 1.555, 0.016) * gaussian(y, -0.148, 0.034)

        delta = Vector((0.0, 0.0, 0.0))
        if ax > 1.0e-6:
            delta.x -= math.copysign(scale * (0.0042 * jaw + 0.0014 * alar), x)
        delta.y += scale * (0.0011 * buccal)
        delta.y -= scale * (0.0025 * malar + 0.0034 * chin + 0.0016 * bridge + 0.0022 * tip)
        delta.z += scale * (0.00045 * malar + 0.00045 * tip - 0.0010 * chin)
        # A restrained left/right difference prevents the planes from reading
        # as a perfectly mirrored procedural mask.
        if x > 0.0:
            delta.y -= scale * 0.00020 * malar

        vertex.co = source + delta
        length = delta.length
        if length <= 1.0e-7:
            continue
        moved += 1
        maximum = max(maximum, length)
        for name, weight in (("jaw", jaw), ("malar", malar), ("buccal", buccal), ("chin", chin), ("nose", bridge + tip + alar)):
            if weight > 0.05:
                zones[name] += 1
    body.data.update()
    return {"movedVertices": moved, "maximumDisplacementM": maximum, "zoneCounts": zones}


def render(camera, variant, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{variant}-{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
for obj in bpy.data.objects:
    if is_hair(obj):
        obj.hide_render = True
body = bpy.data.objects[BODY]
body.data = body.data.copy()
original = [vertex.co.copy() for vertex in body.data.vertices]
camera = bpy.data.objects["Aevrynd Review Camera"]
report = {"source": str(SOURCE), "variants": []}
for scale in (0.0, 1.50, 2.20, 3.00):
    geometry = sculpt(body, original, scale)
    variant = f"{scale:.2f}"
    for name, location, target, lens in (
        ("front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108),
        ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("profile", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88),
        ("low-three-quarter", (0.34, -0.54, 1.50), (0.0, -0.015, 1.565), 96),
    ):
        render(camera, variant, name, location, target, lens)
    report["variants"].append({"scale": scale, "geometry": geometry})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R104_FACE_PLANES_SWEEP=" + json.dumps(report, sort_keys=True))
