import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OFFICIAL = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r109-official-hair-shader-radius-r126-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLYAWAY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"
VARIANTS = (
    ("a-control", None),
    ("b-official-shader-1x", 1.0),
    ("c-official-shader-1p6x", 1.6),
    ("d-official-shader-2p4x", 2.4),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def radius_range(obj):
    attribute = obj.data.attributes.get("radius")
    values = [float(item.value) for item in attribute.data] if attribute else []
    return (min(values), max(values)) if values else (None, None)


def import_official_material():
    with bpy.data.libraries.load(str(OFFICIAL), link=False) as (source, target):
        if "Brown hair" not in source.materials:
            raise RuntimeError("official Brown hair material missing")
        target.materials = ["Brown hair"]
    return target.materials[0]


def apply_variant(factor):
    main = bpy.data.objects[MAIN]
    flyaway = bpy.data.objects[FLYAWAY]
    if factor is not None:
        material = import_official_material()
        for obj in (main, flyaway):
            obj.data.materials.clear()
            obj.data.materials.append(material)
            radius = obj.data.attributes.get("radius")
            if radius:
                for item in radius.data:
                    item.value *= factor
    main_min, main_max = radius_range(main)
    fly_min, fly_max = radius_range(flyaway)
    return {
        "material": main.data.materials[0].name if main.data.materials else None,
        "mainRadiusMinimumUm": main_min * 1.0e6 if main_min is not None else None,
        "mainRadiusMaximumUm": main_max * 1.0e6 if main_max is not None else None,
        "flyawayRadiusMinimumUm": fly_min * 1.0e6 if fly_min is not None else None,
        "flyawayRadiusMaximumUm": fly_max * 1.0e6 if fly_max is not None else None,
    }


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "official": str(OFFICIAL), "license": "CC0", "variants": []}
for name, factor in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    values = apply_variant(factor)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for suffix, location, target, lens in (
        ("01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
        ("04-back", (0.0, 0.72, 1.60), (0.0, 0.015, 1.55), 88),
    ):
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({"name": name, "radiusFactor": factor or 1.0, **values})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_OFFICIAL_HAIR_SHADER_RADIUS_R126=" + json.dumps(report, sort_keys=True))
