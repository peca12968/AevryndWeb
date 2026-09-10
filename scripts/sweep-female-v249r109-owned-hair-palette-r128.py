import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OFFICIAL = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r109-owned-hair-palette-r128-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLYAWAY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
VARIANTS = (
    ("a-control", None),
    ("b-neutral-brown", {"color1": (0.050, 0.028, 0.011, 1.0), "color2": (0.011, 0.0050, 0.0020, 1.0), "random": 0.55}),
    ("c-deep-brown", {"color1": (0.033, 0.014, 0.005, 1.0), "color2": (0.007, 0.0025, 0.0010, 1.0), "random": 0.45}),
    ("d-chestnut", {"color1": (0.070, 0.022, 0.007, 1.0), "color2": (0.016, 0.0040, 0.0015, 1.0), "random": 0.50}),
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
        material.name = "AevryndOwnedLayeredHairMaterial_v249r128"
        group = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeGroup")
        group.inputs["Color 1"].default_value = settings["color1"]
        group.inputs["Color 2"].default_value = settings["color2"]
        group.inputs["Random color"].default_value = settings["random"]
        for obj in (main, flyaway):
            obj.data.materials.clear()
            obj.data.materials.append(material)
        scalp_material = bpy.data.objects[SCALP].data.materials[0]
        principled = next(node for node in scalp_material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
        density = next(node for node in scalp_material.node_tree.nodes if node.bl_idname == "ShaderNodeMath")
        principled.inputs["Base Color"].default_value = settings["color2"]
        principled.inputs["Roughness"].default_value = 0.94
        principled.inputs["Specular IOR Level"].default_value = 0.05
        density.inputs[1].default_value = 0.42
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
print("AEVRYND_OWNED_HAIR_PALETTE_R128=" + json.dumps(report, sort_keys=True))
