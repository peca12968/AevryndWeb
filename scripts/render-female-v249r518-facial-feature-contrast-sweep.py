import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-layered-front-locks-r517.blend"
OUT = ASSETS / "reviews/v249r518-facial-feature-contrast-sweep"
REPORT = ASSETS / "female-v249-mainline-facial-feature-contrast-r518.study.json"
VARIANTS = (
    ("a-r517-current", 0.000038, (0.140, 0.025, 0.020, 1.0)),
    ("b-natural-definition", 0.000050, (0.180, 0.040, 0.035, 1.0)),
    ("c-clear-definition", 0.000058, (0.200, 0.050, 0.040, 1.0)),
    ("d-strong-definition", 0.000066, (0.220, 0.060, 0.050, 1.0)),
)
SHOTS = (
    ("front", (0.0, -0.67, 1.60), (0.0, -0.025, 1.595), 96),
    ("three-quarter", (0.42, -0.58, 1.61), (0.0, -0.015, 1.59), 96),
    ("profile", (0.67, -0.03, 1.61), (0.0, -0.005, 1.59), 96),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "scope": "brow bevel and continuous-body vermilion tint only", "variants": {}}
for label, bevel_depth, lip_color in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    brows = [bpy.data.objects["AevryndFemaleBrow_L_R480"], bpy.data.objects["AevryndFemaleBrow_R_R480"]]
    for brow in brows:
        brow.data.bevel_depth = bevel_depth
    body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
    skin = body.data.materials[0]
    lip = skin.node_tree.nodes["Aevrynd Vermilion Plane Color R484"]
    lip.inputs[2].default_value = lip_color
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    for shot, location, target, lens in SHOTS:
        scene.frame_set(1)
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(OUT / f"{label}-{shot}.png")
        bpy.ops.render.render(write_still=True)
    report["variants"][label] = {
        "browBevelDepthM": bevel_depth,
        "maximumBrowDiameterMicrometers": bevel_depth * 2.0 * 0.78 * 1_000_000.0,
        "lipTargetLinearRGBA": list(lip_color),
        "bodyGeometryChanged": False,
        "lightingChanged": False,
        "exposureChanged": False,
    }
report["status"] = "STUDY_COMPLETE_PENDING_STRICT_VISUAL_SELECTION"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R518_FACIAL_FEATURE_CONTRAST=" + json.dumps({label: {"browBevelM": bevel, "lip": list(color)} for label, bevel, color in VARIANTS}))
