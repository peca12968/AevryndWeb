import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r109-owned-hairline-cards-r115-sweep"
LAYERS = {
    "hairline": "HairlineNaturalCards_v214",
    "crown": "HairCrownCoverage_v212",
    "coverage": "HairCoverageTiles_v246",
}
VARIANTS = (
    ("a-control", ()),
    ("b-hairline-only", ("hairline",)),
    ("c-hairline-crown", ("hairline", "crown")),
    ("d-hairline-coverage", ("hairline", "coverage")),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": []}
for name, enabled in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    enabled_objects = []
    for key in enabled:
        obj = bpy.data.objects[LAYERS[key]]
        obj.hide_render = False
        obj.hide_viewport = False
        enabled_objects.append({
            "name": obj.name,
            "layer": str(obj.get("aevrynd_layer", "")),
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons),
        })
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for suffix, location, target, lens in (
        ("01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({"name": name, "enabled": enabled_objects})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_OWNED_HAIRLINE_CARDS_R115=" + json.dumps(report, sort_keys=True))
