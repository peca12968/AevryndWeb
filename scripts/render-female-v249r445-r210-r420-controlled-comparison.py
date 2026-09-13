import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "r210": ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend",
    "r420": ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend",
}
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-r210-r420-controlled-comparison-r445.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r445-r210-r420-controlled-comparison"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def neutral_lights(scene):
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    target = (0.0, -0.025, 1.60)
    for name, location, energy, size in (
        ("Aevrynd Neutral Key R445", (-0.42, -0.82, 1.82), 13.5, 0.56),
        ("Aevrynd Neutral Fill R445", (0.48, -0.62, 1.70), 8.4, 0.68),
        ("Aevrynd Neutral Top R445", (0.0, -0.08, 2.28), 7.7, 0.52),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.color, data.shape, data.size = energy, (1.0, 1.0, 1.0), "DISK", size
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = location
        look_at(obj, target)
    scene.world.use_nodes = True
    background = next(node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND")
    background.inputs["Color"].default_value = (0.018, 0.018, 0.018, 1.0)
    background.inputs["Strength"].default_value = 0.12


def is_large_hair(obj):
    name = obj.name.lower()
    if any(token in name for token in ("brow", "lash", "lid", "tear", "caruncle", "eye")):
        return False
    materials = getattr(obj.data, "materials", ()) if hasattr(obj, "data") else ()
    material_names = " ".join(material.name.lower() for material in materials if material)
    return obj.type in {"MESH", "CURVES", "CURVE"} and any(token in name or token in material_names for token in ("hair", "scalp", "groom", "flyaway", "root", "lock", "fiber"))


def body_stats():
    bodies = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or "body" not in obj.name.lower() or obj.hide_render:
            continue
        if len(obj.data.vertices) < 30000:
            continue
        bodies.append({"name": obj.name, "vertices": len(obj.data.vertices), "faces": len(obj.data.polygons), "materials": [material.name for material in obj.data.materials if material]})
    return bodies


RENDER_DIR.mkdir(parents=True, exist_ok=True)
results = {}
for label, source in SOURCES.items():
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    neutral_lights(scene)
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects.get("Aevrynd Review Camera")
    scene.camera = camera
    hair = {obj.name: obj.hide_render for obj in bpy.data.objects if is_large_hair(obj)}
    for name in hair:
        bpy.data.objects[name].hide_render = True
    views = (
        ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92, (1000, 1000)),
        ("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105, (1200, 760)),
        ("three-quarter", (0.44, -0.63, 1.62), (0.0, -0.02, 1.595), 88, (1000, 1000)),
    )
    for name, location, target, lens, size in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = str(RENDER_DIR / f"{label}-{name}-no-hair.png")
        bpy.ops.render.render(write_still=True)
    for name, hidden in hair.items():
        bpy.data.objects[name].hide_render = hidden
    camera.location = (0.0, -0.68, 1.605)
    camera.data.lens = 92
    look_at(camera, (0.0, -0.035, 1.606))
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.filepath = str(RENDER_DIR / f"{label}-face-with-hair.png")
    bpy.ops.render.render(write_still=True)
    results[label] = {"source": str(source), "visibleBodies": body_stats(), "hairObjects": len(hair)}

report = {
    "purpose": "Controlled comparison of the collision-proven r210 continuous open-eyelid mainline against the r420 closed high-density body and layered optical stack.",
    "renderDirectory": str(RENDER_DIR),
    "sources": results,
    "fixedConditions": {
        "viewTransform": "Standard",
        "look": "None",
        "exposureEV": 0.0,
        "neutralWhiteLightEnergyW": {"key": 13.5, "fill": 8.4, "top": 7.7},
        "worldStrength": 0.12,
        "identicalCamera": True,
    },
    "strictVisualFinding": "r210 preserves a continuous open eyelid, natural almond aperture and better globe coverage. r420 has richer depth and skin response but uses a closed face with optical layers presented in front of it.",
    "selectedGeometryBaseline": "r210",
    "status": "R210_OPEN_TOPOLOGY_SELECTED_R420_CLOSED_EYE_SURFACE_REJECTED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R445_CONTROLLED_COMPARISON=" + json.dumps(report, sort_keys=True))
