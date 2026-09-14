import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-lip-response-r490.blend"
OUT = ASSETS / "reviews/v249r491-skin-breakup-sweep"
REPORT = ASSETS / "female-v249-mainline-skin-breakup-r491.study.json"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-balanced-skin-r491.blend"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (
    ("baseline", 34.0, (0.085, 0.021, 0.012, 1.0), (0.185, 0.061, 0.035, 1.0)),
    ("scale68-contrast60", 68.0, (0.105, 0.029, 0.017, 1.0), (0.165, 0.053, 0.030, 1.0)),
    ("scale84-contrast40", 84.0, (0.115, 0.033, 0.019, 1.0), (0.155, 0.049, 0.028, 1.0)),
    ("scale90-contrast40", 90.0, (0.115, 0.033, 0.019, 1.0), (0.155, 0.049, 0.028, 1.0)),
    ("scale120-contrast30", 120.0, (0.120, 0.035, 0.020, 1.0), (0.150, 0.047, 0.027, 1.0)),
)
SELECTED_LABEL = "scale84-contrast40"


def look(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens, size):
    camera.location = location
    camera.data.lens = lens
    look(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)


def variant(label, scale, dark_color, light_color):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    material = body.active_material.copy()
    material.name = f"Aevrynd_Skin_Breakup_R491_{label}"
    body.data.materials.clear()
    body.data.materials.append(material)
    noise = material.node_tree.nodes["Aevrynd anatomical tone breakup"]
    ramp = material.node_tree.nodes["Aevrynd restrained melanin range"]
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.58
    noise.inputs["Distortion"].default_value = 0.08
    ramp.color_ramp.elements[0].color = dark_color
    ramp.color_ramp.elements[-1].color = light_color

    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    views = (
        ("face", (0, -0.560, 1.585), (0, -0.060, 1.585), 108, (1100, 1100)),
        ("face-three-quarter", (0.40, -0.570, 1.580), (0, -0.030, 1.560), 92, (1000, 1000)),
        ("full-front", (0, -4.0, 0.90), (0, 0, 0.86), 70, (900, 1200)),
    )
    for name, location, target, lens, size in views:
        render(scene, camera, f"{label}-{name}-f01", location, target, lens, size)
    if label == SELECTED_LABEL:
        scene.frame_set(1)
        scene["aevrynd_revision"] = "v249r491-balanced-skin"
        scene["aevrynd_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_CANDIDATE_AUDITS_PENDING"
        body["aevrynd_skin_breakup_scale"] = scale
        body["aevrynd_skin_breakup_method"] = "higher-frequency restrained-contrast procedural melanin breakup"
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    return {
        "label": label,
        "scale": scale,
        "darkColor": list(dark_color),
        "lightColor": list(light_color),
        "meanEndpointColor": [(dark_color[index] + light_color[index]) * 0.5 for index in range(3)],
        "geometryChanged": False,
    }


OUT.mkdir(parents=True, exist_ok=True)
results = [variant(*settings) for settings in VARIANTS]
report = {
    "revision": "v249r491-study",
    "source": str(SOURCE),
    "method": "preserve mean skin hue while increasing breakup frequency and narrowing endpoint contrast",
    "variants": results,
    "selected": SELECTED_LABEL,
    "output": str(OUTPUT),
    "reviewDirectory": str(OUT),
    "status": "OFFLINE_TECHNICAL_CANDIDATE_AUDITS_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R491_SKIN_BREAKUP=" + json.dumps(report, sort_keys=True))
