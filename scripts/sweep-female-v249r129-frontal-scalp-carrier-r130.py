import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-frontal-scalp-carrier-r130-sweep"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
ATTRIBUTE = "aevrynd_root_density"
VARIANTS = (
    ("a-start-1674-width-14", 1.674, 0.014),
    ("b-start-1680-width-12", 1.680, 0.012),
    ("c-start-1686-width-10", 1.686, 0.010),
)


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def frontal_density(point, start, width):
    side = abs(point.x) / 0.112
    if side >= 1.12:
        return 0.0
    threshold = start + 0.027 * min(1.0, side) ** 1.65
    vertical = smooth((point.z - threshold) / width)
    lateral = 1.0 - smooth((side - 0.94) / 0.18)
    return vertical * lateral


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scalp = bpy.data.objects[SCALP]
attribute = scalp.data.attributes[ATTRIBUTE]
baseline = [item.value for item in attribute.data]
camera = bpy.data.objects["Aevrynd Review Camera"]
report = {"source": str(SOURCE), "geometryChanged": False, "variants": []}

for name, start, width in VARIANTS:
    changed = 0
    for index, vertex in enumerate(scalp.data.vertices):
        world = scalp.matrix_world @ vertex.co
        value = baseline[index]
        if world.y <= -0.035:
            value = frontal_density(world, start, width)
            if abs(value - baseline[index]) > 1e-6:
                changed += 1
        attribute.data[index].value = value
    scalp.data.update()
    for suffix, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({
        "name": name,
        "frontStartM": start,
        "transitionWidthM": width,
        "changedVertices": changed,
    })

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R130_FRONTAL_SCALP_SWEEP=" + json.dumps(report, sort_keys=True))
