import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-multiframe-envelope-tangent-cards-r582-study.blend"
OUT = ASSETS / "reviews/v249r583-collision-safe-tone-sweep"
REPORT = ASSETS / "female-v249-mainline-collision-safe-tone-r583.study.json"
MATERIAL = "Aevrynd_OwnedScalpGuideHair_R582"
STUDY_LAYERS = (
    "AevryndFemaleOwnedScalpGuideGroom_R582_Coverage",
    "AevryndFemaleTangentOuterHairCards_R582",
)
OLD_LAYERS = (
    "AevryndFemaleRuntimeCards_crown_R467",
    "AevryndFemaleRuntimeCards_hairline_R467",
    "AevryndFemaleRuntimeLayeredLocks_front_R517",
    "AevryndFemaleRuntimeLayeredLocks_rear_R506",
)
VARIANTS = (
    ("a-r569-current", None),
    ("b-r582-direct-base", (0.0350, 0.0120, 0.0050, 1.0)),
    ("c-direct-plus-10", (0.0385, 0.0132, 0.0055, 1.0)),
    ("d-direct-plus-20", (0.0420, 0.0144, 0.0060, 1.0)),
    ("e-direct-plus-30", (0.0455, 0.0156, 0.0065, 1.0)),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
hair_node = next(node for node in bpy.data.materials[MATERIAL].node_tree.nodes if node.type == "BSDF_HAIR_PRINCIPLED")
report_variants = {}
for label, colour in VARIANTS:
    show_study = colour is not None
    for name in STUDY_LAYERS:
        bpy.data.objects[name].hide_render = not show_study
        bpy.data.objects[name].hide_viewport = not show_study
    for name in OLD_LAYERS:
        bpy.data.objects[name].hide_render = show_study
        bpy.data.objects[name].hide_viewport = show_study
    if colour is not None:
        hair_node.parametrization = "COLOR"
        hair_node.inputs["Color"].default_value = colour
    for view, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        ("profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
        ("back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.58), 88),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens)
    report_variants[label] = {"linearRGBA": colour}

report = {
    "source": str(SOURCE),
    "method": "hold r582 geometry, collision envelope, lights and color management fixed; sweep only the direct linear-RGBA coverage color around the r579 selected dark-warm bound",
    "variants": report_variants,
    "collisionBasis": "r582 four-frame body and clothing PASS; material-only sweep cannot change geometry",
    "status": "VISUAL_TONE_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R583_COLLISION_SAFE_TONE=" + json.dumps(report, sort_keys=True))
