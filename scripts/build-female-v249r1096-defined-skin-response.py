"""Preserve face-scale skin detail and establish an AgX review transform for r1091."""
from pathlib import Path
import json

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-scalp-overlay-r1091-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-defined-skin-response-r1096-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1096-defined-skin-response.build-report.json"
RENDER_REPORT = ASSETS / "female-v249-mainline-r1096-defined-skin-response.render.json"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1096-defined-skin-response"
BODY = "AevryndFemaleCC0BalancedEyeOptics_R1080"
SKIN = "Aevrynd_CC0_RegionalSkin_R1082_c-balanced"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def tune_skin(material):
    nodes = material.node_tree.nodes
    primary = nodes["凹凸"]
    secondary = nodes["Aevrynd Secondary Micro Pore Normal R1082"]
    bsdf = nodes["原則化 BSDF"]
    before = {
        "primaryStrength": primary.inputs["Strength"].default_value,
        "primaryDistanceM": primary.inputs["Distance"].default_value,
        "secondaryStrength": secondary.inputs["Strength"].default_value,
        "secondaryDistanceM": secondary.inputs["Distance"].default_value,
        "subsurfaceWeight": bsdf.inputs["Subsurface Weight"].default_value,
        "subsurfaceScaleM": bsdf.inputs["Subsurface Scale"].default_value,
    }
    primary.inputs["Strength"].default_value = 0.125
    primary.inputs["Distance"].default_value = 0.000120
    secondary.inputs["Strength"].default_value = 0.055
    secondary.inputs["Distance"].default_value = 0.000025
    bsdf.inputs["Subsurface Weight"].default_value = 0.035
    bsdf.inputs["Subsurface Scale"].default_value = 0.0032
    after = {
        "primaryStrength": primary.inputs["Strength"].default_value,
        "primaryDistanceM": primary.inputs["Distance"].default_value,
        "secondaryStrength": secondary.inputs["Strength"].default_value,
        "secondaryDistanceM": secondary.inputs["Distance"].default_value,
        "subsurfaceWeight": bsdf.inputs["Subsurface Weight"].default_value,
        "subsurfaceScaleM": bsdf.inputs["Subsurface Scale"].default_value,
    }
    return {"before": before, "after": after}


def render(scene, view):
    camera = scene.camera
    settings = {
        "front": ((0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88),
        "three-quarter": ((0.45, -0.62, 1.46), (0.0, -0.015, 1.445), 88),
        "profile": ((0.67, -0.10, 1.46), (0.0, -0.015, 1.445), 92),
        "back": ((0.0, 0.72, 1.445), (0.0, 0.025, 1.445), 88),
    }
    camera.location, target, camera.data.lens = settings[view]
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / f"r1096-{view}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = -0.5
scene.view_settings.gamma = 1.0
material_report = tune_skin(bpy.data.materials[SKIN])
body = bpy.data.objects[BODY]
body["aevrynd_revision"] = "v249r1096-defined-skin-response"
body["aevrynd_skin_review_transform"] = "AgX - Medium High Contrast, exposure -0.5"
scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
scene["aevrynd_website_promotion"] = "forbidden"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

RENDER_DIR.mkdir(parents=True, exist_ok=True)
renders = [render(scene, view) for view in ("front", "three-quarter", "profile", "back")]
report = {
    "revision": "v249r1096-defined-skin-response",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "increase two-scale owned procedural skin normal response, reduce broad subsurface blur, and use an AgX review transform that preserves highlights",
    "material": material_report,
    "colorManagement": {"viewTransform": "AgX", "look": "AgX - Medium High Contrast", "exposure": -0.5, "gamma": 1.0},
    "geometryChanged": False,
    "collisionStatus": "INHERITED_R1091_GEOMETRY_UNCHANGED",
    "ownership": "Aevrynd-authored procedural material parameters; no external textures or runtime dependencies added",
    "externalDependencies": [],
    "status": "PASS",
    "websitePromotionApproved": False
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
RENDER_REPORT.write_text(json.dumps({"revision": report["revision"], "source": str(OUTPUT), "renders": renders}, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1096_SKIN=" + json.dumps({"material": material_report, "renders": len(renders), "status": report["status"]}, sort_keys=True))
