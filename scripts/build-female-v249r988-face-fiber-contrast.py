"""Tune the restored target-fitted brow/lash fibres for readable facial contrast."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-face-fiber-restore-r987.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-face-fiber-contrast-r988.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-face-fiber-contrast-r988.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r988-face-fiber-contrast"


def set_principled(material_name, color, roughness, alpha=1.0):
    mat = bpy.data.materials[material_name]
    for node in mat.node_tree.nodes:
        if node.bl_idname == "ShaderNodeBsdfPrincipled":
            node.inputs["Base Color"].default_value = (*color, 1.0)
            node.inputs["Roughness"].default_value = roughness
            node.inputs["Alpha"].default_value = alpha
            if "Specular IOR Level" in node.inputs:
                node.inputs["Specular IOR Level"].default_value = 0.22
    return material_name


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
tuned = [
    set_principled("Aevrynd_Brow_Density_v39", (0.040, 0.010, 0.004), 0.72),
    set_principled("Aevrynd_Brow_Hair_v39_Dark", (0.022, 0.004, 0.0015), 0.58),
    set_principled("Aevrynd_Brow_Hair_v39_Warm", (0.060, 0.014, 0.004), 0.60),
    set_principled("Aevrynd_Lash_Hair_v51", (0.006, 0.0015, 0.0008), 0.56),
]
scene["aevrynd_mainline_revision"] = "v249r988-face-fiber-contrast"
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
report = {"source": str(SOURCE), "output": str(OUTPUT), "tunedMaterials": tuned,
          "geometryChanged": False, "websitePromotionApproved": False,
          "status": "STRICT_VISUAL_REVIEW_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R988_FACE_FIBER_CONTRAST=" + json.dumps(report, sort_keys=True))
