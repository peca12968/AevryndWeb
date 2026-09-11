import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-integrated-eye-shader-r328.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-exposure-calibration-r330.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r330-exposure-calibration"
VARIANTS = (("a-current-0ev", 0.0), ("b-plus-0p25ev", 0.25), ("c-plus-0p50ev", 0.50))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
camera.location = (0.0, -0.68, 1.605)
camera.data.lens = 92
look_at(camera, (0.0, -0.035, 1.606))
renders = {}
for label, exposure in VARIANTS:
    scene.view_settings.exposure = exposure
    scene.render.resolution_x = scene.render.resolution_y = 1000
    path = RENDER_DIR / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    renders[label] = {"exposureEV": exposure, "path": str(path)}
scene.view_settings.exposure = 0.0
report = {
    "source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "variants": renders,
    "purpose": "Separate actual skin-tone drift from display exposure and local eye-contrast effects using one fixed camera and unchanged materials/lights.",
    "status": "PIXEL_MEASUREMENT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R330_EXPOSURE_CALIBRATION=" + json.dumps(report, sort_keys=True))
