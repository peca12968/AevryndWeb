import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
GROOM_SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-zero-penetration-root-veil-v368.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r109-owned-groom-transplant-r112-sweep"
RIG = "AevryndFemaleRig"
CURRENT_HAIR = (
    "AevryndFemaleCC0LongHairStudyMain_v249r85",
    "AevryndFemaleCC0LongHairStudyFlyaway_v249r85",
)
MAIN_LAYERS = (
    "AevryndFemaleHair_ContinuousFlow_v317_L",
    "AevryndFemaleHair_ContinuousFlow_v317_R",
    "AevryndFemaleHair_ShapedOverlay_v319_L",
    "AevryndFemaleHair_ShapedOverlay_v319_R",
)
VEIL_LAYERS = (
    "AevryndFemaleHair_CrownRootVeil_v338_L",
    "AevryndFemaleHair_CrownRootVeil_v338_R",
)
VARIANTS = (
    ("a-control-r109", False, None),
    ("b-owned-main-overlay", True, None),
    ("c-owned-with-veil-0p60", True, 0.60),
    ("d-owned-with-veil-1p00", True, 1.00),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def append_groom(names):
    with bpy.data.libraries.load(str(GROOM_SOURCE), link=False) as (data_from, data_to):
        missing = [name for name in names if name not in data_from.objects]
        if missing:
            raise RuntimeError(f"owned groom layers missing: {missing}")
        data_to.objects = list(names)
    result = []
    rig = bpy.data.objects[RIG]
    for obj in data_to.objects:
        if obj is None:
            continue
        bpy.context.scene.collection.objects.link(obj)
        bpy.context.view_layer.update()
        world = obj.matrix_world.copy()
        obj.parent = rig
        obj.parent_type = "BONE"
        obj.parent_bone = "head"
        obj.matrix_world = world
        obj.hide_render = False
        obj.hide_viewport = False
        obj["aevrynd_revision"] = "v249r112-transplant-sweep"
        obj["aevrynd_source"] = "Aevrynd-owned guide groom v368"
        result.append(obj)
    return result


def scale_radius(obj, factor):
    attribute = obj.data.attributes.get("radius")
    if attribute is None:
        return {"points": 0, "minimumM": None, "maximumM": None}
    values = []
    for item in attribute.data:
        item.value *= factor
        values.append(item.value)
    return {"points": len(values), "minimumM": min(values), "maximumM": max(values)}


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "groomSource": str(GROOM_SOURCE), "variants": []}
for variant, transplant, veil_factor in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    imported = []
    radius_report = {}
    if transplant:
        for name in CURRENT_HAIR:
            obj = bpy.data.objects.get(name)
            if obj:
                obj.hide_render = True
                obj.hide_viewport = True
        names = MAIN_LAYERS + (VEIL_LAYERS if veil_factor is not None else ())
        imported = append_groom(names)
        if veil_factor is not None:
            for obj in imported:
                if obj.name in VEIL_LAYERS:
                    radius_report[obj.name] = scale_radius(obj, veil_factor)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for suffix, location, target, lens in (
        ("01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
        ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ):
        render(camera, f"{variant}-{suffix}", location, target, lens)
    report["variants"].append({
        "name": variant,
        "transplant": transplant,
        "veilRadiusFactor": veil_factor,
        "visibleImportedLayers": [obj.name for obj in imported],
        "radius": radius_report,
    })

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_OWNED_GROOM_TRANSPLANT_R112=" + json.dumps(report, sort_keys=True))
