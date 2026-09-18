"""Render a strict multi-angle full-head scorecard from the r1076 face baseline."""
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-commissure-curvature-r1076-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1077-full-head-scorecard.render.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1077-full-head-scorecard"
BODY = "AevryndFemaleCC0CommissureCurvature_R1076"
HAIR = ("AevryndFemaleTargetScalp_R976", "AevryndFemaleCoherentClumpGroom_R981")


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def set_hair(visible):
    for name in HAIR:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = not visible


def render(scene, camera, label, location, target, lens=88, size=(1000, 1000)):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
OUT.mkdir(parents=True, exist_ok=True)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
camera = scene.camera
views = []

set_hair(False)
face_views = (
    ("01-face-front", (0.0, -0.72, 1.445), (0.0, -0.025, 1.440), 88, (1000, 1000)),
    ("02-face-left-three-quarter", (0.45, -0.62, 1.460), (0.0, -0.015, 1.440), 88, (1000, 1000)),
    ("03-face-right-three-quarter", (-0.45, -0.62, 1.460), (0.0, -0.015, 1.440), 88, (1000, 1000)),
    ("04-face-left-profile", (0.70, -0.03, 1.450), (0.0, -0.015, 1.440), 92, (1000, 1000)),
    ("05-face-right-profile", (-0.70, -0.03, 1.450), (0.0, -0.015, 1.440), 92, (1000, 1000)),
    ("06-face-low", (0.0, -0.68, 1.330), (0.0, -0.015, 1.435), 88, (1000, 1000)),
    ("07-face-high", (0.0, -0.66, 1.620), (0.0, -0.015, 1.430), 88, (1000, 1000)),
    ("08-eye-front", (0.0, -0.405, 1.449), (0.0, -0.105, 1.449), 135, (1400, 760)),
    ("09-eye-oblique", (0.235, -0.405, 1.451), (0.0, -0.105, 1.449), 135, (1400, 760)),
)
for args in face_views:
    views.append({"hair": False, "label": args[0], "path": render(scene, camera, *args)})

set_hair(True)
hair_views = (
    ("10-hair-front", (0.0, -0.72, 1.445), (0.0, -0.025, 1.440), 88, (1000, 1000)),
    ("11-hair-left-three-quarter", (0.45, -0.62, 1.460), (0.0, -0.015, 1.440), 88, (1000, 1000)),
    ("12-hair-right-three-quarter", (-0.45, -0.62, 1.460), (0.0, -0.015, 1.440), 88, (1000, 1000)),
    ("13-hair-profile", (0.70, -0.03, 1.450), (0.0, -0.015, 1.440), 92, (1000, 1000)),
    ("14-hair-back", (0.0, 0.72, 1.445), (0.0, 0.025, 1.440), 88, (1000, 1000)),
    ("15-hair-top", (0.0, -0.25, 2.00), (0.0, 0.015, 1.510), 78, (1000, 1000)),
)
for args in hair_views:
    views.append({"hair": True, "label": args[0], "path": render(scene, camera, *args)})

hair_summary = []
for name in HAIR:
    obj = bpy.data.objects.get(name)
    if not obj:
        continue
    hair_summary.append({
        "name": name, "type": obj.type,
        "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
        "points": sum(len(curve.points) for curve in obj.data.curves) if obj.type == "CURVES" else None,
        "materials": [material.name if material else None for material in obj.data.materials],
    })

report = {
    "revision": "v249r1077-full-head-scorecard-render", "source": str(SOURCE), "body": BODY,
    "lightingContract": "Standard/None exposure 0.0, inherited Aevrynd key/fill/rim lights",
    "views": views, "hairLayers": hair_summary,
    "modelModified": False, "websitePromotionApproved": False,
    "status": "VISUAL_SCORING_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1077_SCORECARD=" + json.dumps({"views": len(views), "hairLayers": hair_summary}, sort_keys=True))
