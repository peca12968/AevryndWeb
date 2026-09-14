import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-layered-rear-locks-r506.blend"
OUT = ASSETS / "reviews/v249r509-skin-tone-sweep"
REPORT = ASSETS / "female-v249-mainline-skin-tone-r509.study.json"
VARIANTS = (
    ("a-r506-current", ((0.115, 0.033, 0.019, 1.0), (0.155, 0.049, 0.028, 1.0))),
    ("b-lighter-neutral", ((0.145, 0.050, 0.032, 1.0), (0.188, 0.070, 0.042, 1.0))),
    ("c-medium-neutral", ((0.175, 0.068, 0.046, 1.0), (0.220, 0.092, 0.060, 1.0))),
    ("d-light-warm", ((0.205, 0.087, 0.063, 1.0), (0.253, 0.116, 0.080, 1.0))),
)
SHOTS = (
    ("face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (900, 900)),
    ("face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88, (900, 900)),
    ("full-front", (0.0, -4.0, 0.90), (0.0, 0.0, 0.86), 70, (675, 900)),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def luminance(color):
    return 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
material = body.data.materials[0]
ramp = material.node_tree.nodes["Aevrynd restrained melanin range"].color_ramp
report = {
    "source": str(SOURCE),
    "scope": "material-only melanin ramp study; geometry, lights, exposure, hair and clothing unchanged",
    "variants": {},
}
for label, colors in VARIANTS:
    ramp.elements[0].color = colors[0]
    ramp.elements[1].color = colors[1]
    for shot, location, target, lens, resolution in SHOTS:
        scene.frame_set(1)
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.filepath = str(OUT / f"{label}-{shot}.png")
        bpy.ops.render.render(write_still=True)
    report["variants"][label] = {
        "rampLinearRGBA": [list(color) for color in colors],
        "rampLuminance": [luminance(color) for color in colors],
        "geometryChanged": False,
        "lightingChanged": False,
        "exposureChanged": False,
    }
report["status"] = "STUDY_COMPLETE_PENDING_STRICT_VISUAL_AND_PIXEL_REVIEW"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R509_SKIN_TONE_SWEEP=" + json.dumps({label: value["rampLuminance"] for label, value in report["variants"].items()}))
