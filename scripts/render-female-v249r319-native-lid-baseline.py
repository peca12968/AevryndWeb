import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-optical-stack-r318.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-native-lid-baseline-r319.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r319-native-lid-baseline"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
hidden = []
for side in ("L", "R"):
    obj = bpy.data.objects.get(f"AevryndEye_{side}_UpperLidSurface_R308")
    if obj:
        obj.hide_render = True
        hidden.append(obj.name)

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("face-close", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
)
for name, location, target, lens in views:
    scene.frame_set(1)
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE),
    "hiddenTransitionalLayers": hidden,
    "renderDirectory": str(RENDER_DIR),
    "purpose": "Measure the native dense body aperture after the r318 collision-safe optical correction, without the r308 upper-lid overlay.",
    "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R319_NATIVE_LID_BASELINE=" + json.dumps(report, sort_keys=True))
