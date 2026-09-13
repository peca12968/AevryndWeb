import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-authored-primary-locks-r454-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-r455-primary-lock-balance-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r455-primary-lock-balance-sweep"
BASE = tuple(f"AevryndFemale{region}SurfaceFlow_R383" for region in ("Front", "Crown", "Rear"))
PRIMARY = tuple(f"AevryndFemaleAuthoredPrimaryLocks_{region}_R454" for region in ("Front", "Crown", "Rear"))
VARIANTS = (
    ("a-control", 1.00, 1.00),
    ("b-balanced", 0.72, 1.60),
    ("c-bold", 0.52, 2.20),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
scene.frame_set(1)
base_objects = [bpy.data.objects[name] for name in BASE]
primary_objects = [bpy.data.objects[name] for name in PRIMARY]
original = {
    obj.name: [item.value for item in obj.data.attributes["radius"].data]
    for obj in base_objects + primary_objects
}
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for variant, base_scale, primary_scale in VARIANTS:
    for obj in base_objects:
        for item, value in zip(obj.data.attributes["radius"].data, original[obj.name]):
            item.value = value * base_scale
    for obj in primary_objects:
        for item, value in zip(obj.data.attributes["radius"].data, original[obj.name]):
            item.value = value * primary_scale
    bpy.context.view_layer.update()
    for view, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("hairline", (0.0, -0.57, 1.76), (0.0, -0.02, 1.64), 92),
        ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        ("back", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
    ):
        render(scene, camera, f"{variant}-{view}", location, target, lens)

report = {
    "model": str(MODEL),
    "renderDirectory": str(RENDER_DIR),
    "baseLayers": list(BASE),
    "primaryLayers": list(PRIMARY),
    "variants": [
        {"name": name, "baseRadiusScaleFromR454": base, "primaryRadiusScaleFromR454": primary}
        for name, base, primary in VARIANTS
    ],
    "geometryChanged": False,
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R455_PRIMARY_LOCK_BALANCE_SWEEP=" + json.dumps(report, sort_keys=True))
