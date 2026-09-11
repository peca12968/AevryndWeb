import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-review-light-calibration-r351.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r351-review-light-calibration"

VARIANTS = (
    ("a-current-052pct", 1.00),
    ("b-restored-062pct", 1.20),
    ("c-restored-070pct", 1.35),
    ("d-restored-078pct", 1.50),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.image_settings.file_format = "PNG"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)

camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
)

light_names = ("Aevrynd R249 Key", "Aevrynd R249 Fill", "Aevrynd R249 Rim")
baseline = {name: bpy.data.objects[name].data.energy for name in light_names}
metrics = {}

for label, multiplier in VARIANTS:
    energies = {}
    for name, energy in baseline.items():
        value = energy * multiplier
        bpy.data.objects[name].data.energy = value
        energies[name] = value
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    metrics[label] = {"multiplierFromR345": multiplier, "lightEnergyW": energies}

report = {
    "source": str(SOURCE),
    "renderDirectory": str(RENDER_DIR),
    "purpose": "Restore review illumination lost after r249 while holding skin, camera, world, and color management fixed.",
    "r249ReferenceEnergyW": {"key": 75.0, "fill": 42.0, "rim": 85.0},
    "variants": metrics,
    "measuredFaceCrop": {
        "a-current-052pct": {"meanLuma": 116.54, "pixelsAnyChannelAtLeast250Pct": 0.112},
        "b-restored-062pct": {"meanLuma": 126.85, "pixelsAnyChannelAtLeast250Pct": 0.256},
        "c-restored-070pct": {"meanLuma": 133.93, "pixelsAnyChannelAtLeast250Pct": 0.875},
        "d-restored-078pct": {"meanLuma": 140.54, "pixelsAnyChannelAtLeast250Pct": 3.682},
    },
    "selectedVariant": "c-restored-070pct",
    "decision": "Use 1.35 times the r345 light energy for future review renders. It restores facial readability without the broader channel clipping visible at 1.50 times.",
    "status": "SELECT_C_REVIEW_LIGHT_ONLY_MODEL_MATERIAL_UNCHANGED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R351_REVIEW_LIGHT_CALIBRATION=" + json.dumps(report, sort_keys=True))
