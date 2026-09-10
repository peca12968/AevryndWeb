import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-main-hair-front-band-mask-r139-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
VARIANTS = (
    ("a-baseline", None),
    ("b-mask-y-120-100", (-0.120, -0.100)),
    ("c-mask-y-120-080", (-0.120, -0.080)),
    ("d-mask-y-130-060", (-0.130, -0.060)),
)


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
main = bpy.data.objects[MAIN]
matrix = main.matrix_world
radius = main.data.attributes["radius"]
original = [item.value for item in radius.data]
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)
report = {"source": str(SOURCE), "variants": []}

for name, y_band in VARIANTS:
    for index, value in enumerate(original):
        radius.data[index].value = value
    masked = []
    if y_band:
        for point_index, point in enumerate(main.data.points):
            world = matrix @ point.position
            if (
                abs(world.x) <= 0.125
                and y_band[0] <= world.y <= y_band[1]
                and 1.625 <= world.z <= 1.735
            ):
                radius.data[point_index].value = 0.0
                masked.append(point_index)
    bpy.context.view_layer.update()
    for suffix, location, target, lens in views:
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({
        "name": name,
        "yBandM": list(y_band) if y_band else None,
        "maskedPointCount": len(masked),
        "maskedPointIndicesSample": masked[:40],
    })

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R139_MAIN_HAIR_BAND_MASK=" + json.dumps(report, sort_keys=True))
