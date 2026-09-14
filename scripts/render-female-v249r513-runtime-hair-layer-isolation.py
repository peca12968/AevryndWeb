import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-lighter-neutral-skin-r510.blend"
OUT = ASSETS / "reviews/v249r513-runtime-hair-layer-isolation"
REPORT = ASSETS / "female-v249-mainline-runtime-hair-layer-isolation-r513.study.json"
FRONT = "AevryndFemaleRuntimeCards_front_R467"
CROWN = "AevryndFemaleRuntimeCards_crown_R467"
REAR = "AevryndFemaleRuntimeLayeredLocks_rear_R506"
HAIRLINE = "AevryndFemaleRuntimeCards_hairline_R467"
FOUNDATION = (
    "AevryndFemaleRuntimeScalpCap_R467",
    "AevryndFemaleRuntimeHairlineDensity_R467",
    "AevryndFemaleRuntimePartRootDensity_R467",
)
VISIBLE = (FRONT, CROWN, REAR, HAIRLINE, *FOUNDATION)
CASES = (
    ("all", VISIBLE),
    ("front", (*FOUNDATION, FRONT)),
    ("crown", (*FOUNDATION, CROWN)),
    ("rear", (*FOUNDATION, REAR)),
    ("hairline", (*FOUNDATION, HAIRLINE)),
    ("foundation", FOUNDATION),
)
SHOTS = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
report = {"source": str(SOURCE), "cases": {}}
for label, enabled in CASES:
    for name in VISIBLE:
        bpy.data.objects[name].hide_render = name not in enabled
    for shot, location, target, lens in SHOTS:
        scene.frame_set(1)
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(OUT / f"{label}-{shot}.png")
        bpy.ops.render.render(write_still=True)
    report["cases"][label] = {"enabled": list(enabled), "shots": [value[0] for value in SHOTS]}
report["status"] = "DIAGNOSTIC_COMPLETE_PENDING_VISUAL_ATTRIBUTION"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R513_RUNTIME_HAIR_LAYER_ISOLATION=" + json.dumps({label: list(enabled) for label, enabled in CASES}))
