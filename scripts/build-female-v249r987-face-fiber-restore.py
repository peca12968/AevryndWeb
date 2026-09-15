"""Restore the already target-fitted owned brow and lash layers onto r981."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-coherent-clump-waves-r981.blend"
FEATURE_SOURCE = ASSETS / "aevrynd-female-cc0-hair-feature-fit-r974.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-face-fiber-restore-r987.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-face-fiber-restore-r987.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r987-face-fiber-restore"
RIG = "AevryndFemaleRig"
FEATURES = (
    "Brow_L", "Brow_L_Density", "Brow_R", "Brow_R_Density",
    "Eye_L_LowerLashes", "Eye_L_UpperLashes",
    "Eye_R_LowerLashes", "Eye_R_UpperLashes",
)


def bind_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
with bpy.data.libraries.load(str(FEATURE_SOURCE), link=False) as (src, dst):
    missing = [name for name in FEATURES if name not in src.objects]
    if missing:
        raise RuntimeError("Missing fitted feature objects: " + ", ".join(missing))
    dst.objects = list(FEATURES)

rig = bpy.data.objects[RIG]
loaded = []
for obj in dst.objects:
    scene.collection.objects.link(obj)
    bind_head(obj, rig)
    obj["aevrynd_layer"] = "face.feature.target_fitted"
    obj["aevrynd_revision"] = "v249r987"
    obj["aevrynd_transfer_source"] = FEATURE_SOURCE.name
    loaded.append(obj.name)

scene["aevrynd_mainline_revision"] = "v249r987-face-fiber-restore"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "FACE_FEATURE_VISUAL_STUDY_PENDING_STRICT_REVIEW"
scene["aevrynd_website_promotion"] = "forbidden pending facial motion and runtime gates"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects.get("Aevrynd Review Camera") or scene.camera
scene.camera = camera
for args in (
    ("01-face-front", (0.0, -0.68, 1.49), (0.0, -0.055, 1.48), 88),
    ("02-face-three-quarter", (0.42, -0.58, 1.51), (0.0, -0.045, 1.48), 88),
    ("03-face-profile", (0.68, -0.02, 1.50), (0.0, -0.035, 1.48), 90),
    ("04-eye-front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.485), 105),
    ("05-eye-three-quarter", (0.30, -0.40, 1.49), (0.0, -0.055, 1.485), 105),
    ("06-full-three-quarter", (1.10, -1.62, 1.22), (0.0, -0.01, 0.92), 58),
):
    render(scene, camera, *args)

report = {
    "source": str(SOURCE), "featureSource": str(FEATURE_SOURCE), "output": str(OUTPUT),
    "featureObjects": loaded, "featureObjectCount": len(loaded),
    "existingR981GroomChanged": False, "websitePromotionApproved": False,
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R987_FACE_FIBER_RESTORE=" + json.dumps(report, sort_keys=True))
