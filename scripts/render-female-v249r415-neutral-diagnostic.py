import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "r345": ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend",
    "r413": ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-orbital-folds-r413.blend",
}
OUT = ROOT.parent / "Temp/female-realism/v249r415-neutral-diagnostic"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-neutral-diagnostic-r415.study.json"
BODY = "AevryndFemaleBody_CC0_R249"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def build_neutral_light(scene):
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)

    specs = (
        ("Aevrynd Neutral Key R415", (-0.42, -0.82, 1.82), 39.0, 0.56),
        ("Aevrynd Neutral Fill R415", (0.48, -0.62, 1.70), 24.0, 0.68),
        ("Aevrynd Neutral Top R415", (0.00, -0.08, 2.28), 22.0, 0.52),
    )
    target = (0.0, -0.025, 1.60)
    for name, location, energy, size in specs:
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.color = (1.0, 1.0, 1.0)
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = location
        look_at(obj, target)

    world = scene.world or bpy.data.worlds.new("Aevrynd Neutral World R415")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is None:
        world.node_tree.nodes.clear()
        background = world.node_tree.nodes.new("ShaderNodeBackground")
        output = world.node_tree.nodes.new("ShaderNodeOutputWorld")
        world.node_tree.links.new(background.outputs["Background"], output.inputs["Surface"])
    background.inputs["Color"].default_value = (0.018, 0.018, 0.018, 1.0)
    background.inputs["Strength"].default_value = 0.35


def build_clay_material():
    material = bpy.data.materials.new("Aevrynd Neutral Anatomy Clay R415")
    material.use_nodes = True
    material.diffuse_color = (0.24, 0.105, 0.070, 1.0)
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (0.24, 0.105, 0.070, 1.0)
    shader.inputs["Roughness"].default_value = 0.56
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Specular IOR Level"].default_value = 0.18
    shader.inputs["Subsurface Weight"].default_value = 0.0
    return material


def is_large_hair_object(obj):
    name = obj.name.lower()
    preserve = ("brow", "lash", "lid", "tear", "caruncle", "eye")
    if any(token in name for token in preserve):
        return False
    if any(token in name for token in ("hair", "scalp", "groom", "flyaway", "root", "lock")):
        return True
    if obj.type in {"MESH", "CURVES", "CURVE"}:
        materials = getattr(obj.data, "materials", ())
        material_names = " ".join(material.name.lower() for material in materials if material)
        return any(token in material_names for token in ("hair", "scalp", "groom", "fiber"))
    return False


def render_source(label, source):
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Base Contrast"
    scene.view_settings.exposure = 0.0
    build_neutral_light(scene)

    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects.get("Aevrynd Review Camera")
    if camera is None:
        raise RuntimeError("Review camera not found")
    scene.camera = camera
    body = bpy.data.objects[BODY]
    hair_visibility = {obj.name: obj.hide_render for obj in bpy.data.objects if is_large_hair_object(obj)}
    original_materials = list(body.data.materials)

    for obj_name in hair_visibility:
        bpy.data.objects[obj_name].hide_render = True

    views = (
        ("face-front", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
        ("eyes-close", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105),
        ("face-three-quarter", (0.44, -0.63, 1.62), (0.0, -0.02, 1.595), 88),
    )

    for mode in ("material", "clay"):
        if mode == "clay":
            body.data = body.data.copy()
            body.data.materials.clear()
            body.data.materials.append(build_clay_material())
        for view_name, location, target, lens in views:
            camera.location = location
            camera.data.lens = lens
            look_at(camera, target)
            scene.render.filepath = str(OUT / f"{label}-{mode}-{view_name}.png")
            bpy.ops.render.render(write_still=True)

    return {
        "source": str(source),
        "bodyMaterialSlots": [material.name if material else None for material in original_materials],
        "hiddenHairObjects": sorted(hair_visibility),
        "geometryChanged": False,
        "materialsChangedInSource": False,
    }


OUT.mkdir(parents=True, exist_ok=True)
results = {label: render_source(label, source) for label, source in SOURCES.items()}
report = {
    "purpose": "Separate facial-form review from the warm/cool cinematic rig and black-background hair contrast.",
    "renderDirectory": str(OUT),
    "sources": results,
    "fixedConditions": {
        "lightColor": [1.0, 1.0, 1.0],
        "lightEnergyW": {"key": 39.0, "fill": 24.0, "top": 22.0},
        "worldColorLinear": [0.018, 0.018, 0.018],
        "worldStrength": 0.35,
        "viewTransform": "AgX",
        "look": "AgX - Base Contrast",
        "exposureEV": 0.0,
        "largeHairHidden": True,
        "clayBodyOnly": True,
    },
    "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R415_NEUTRAL_DIAGNOSTIC=" + json.dumps(report, sort_keys=True))
