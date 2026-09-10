import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OFFICIAL = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r109-official-hair-scalp-match-r127-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLYAWAY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
VARIANTS = (
    ("a-control", None),
    ("b-official-current-scalp", {}),
    ("c-official-root-color-0p42", {"color": (0.03125, 0.01639, 0.00429, 1.0), "density": 0.42}),
    ("d-official-warm-root-0p32", {"color": (0.0550, 0.0180, 0.0080, 1.0), "density": 0.32}),
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


def apply_variant(settings):
    main = bpy.data.objects[MAIN]
    flyaway = bpy.data.objects[FLYAWAY]
    if settings is not None:
        material = import_official_material()
        for obj in (main, flyaway):
            obj.data.materials.clear()
            obj.data.materials.append(material)
        if settings:
            scalp_material = bpy.data.objects[SCALP].data.materials[0]
            principled = next(node for node in scalp_material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
            density = next(node for node in scalp_material.node_tree.nodes if node.bl_idname == "ShaderNodeMath")
            principled.inputs["Base Color"].default_value = settings["color"]
            principled.inputs["Roughness"].default_value = 0.94
            principled.inputs["Specular IOR Level"].default_value = 0.05
            density.inputs[1].default_value = settings["density"]
    main_min, main_max = radius_range(main)
    fly_min, fly_max = radius_range(flyaway)
    scalp_material = bpy.data.objects[SCALP].data.materials[0]
    scalp_principled = next(node for node in scalp_material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    scalp_density = next(node for node in scalp_material.node_tree.nodes if node.bl_idname == "ShaderNodeMath")
    return {
        "material": main.data.materials[0].name if main.data.materials else None,
        "mainRadiusMinimumUm": main_min * 1.0e6 if main_min is not None else None,
        "mainRadiusMaximumUm": main_max * 1.0e6 if main_max is not None else None,
        "flyawayRadiusMinimumUm": fly_min * 1.0e6 if fly_min is not None else None,
        "flyawayRadiusMaximumUm": fly_max * 1.0e6 if fly_max is not None else None,
        "scalpBaseColor": list(scalp_principled.inputs["Base Color"].default_value),
        "scalpDensityStrength": float(scalp_density.inputs[1].default_value),
    }


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "official": str(OFFICIAL), "license": "CC0", "variants": []}
for name, settings in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    values = apply_variant(settings)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for suffix, location, target, lens in (
        ("01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
        ("04-back", (0.0, 0.72, 1.60), (0.0, 0.015, 1.55), 88),
    ):
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({"name": name, **values})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_OFFICIAL_HAIR_SCALP_MATCH_R127=" + json.dumps(report, sort_keys=True))
