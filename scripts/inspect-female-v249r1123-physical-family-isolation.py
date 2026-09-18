"""Physically isolate each r1123 groom family for reliable visual attribution."""
from pathlib import Path
import json

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-rear-contour-r1123-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1125-physical-family-isolation.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1125-physical-family-isolation"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
FAMILY = "aevrynd_family_r1087"


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, view):
    camera = scene.camera
    if view == "front":
        camera.location, target, camera.data.lens, size = (0.0, -1.05, 1.43), (0.0, 0.0, 1.40), 72, (1000, 1000)
    elif view == "hairline":
        camera.location, target, camera.data.lens, size = (0.0, -0.53, 1.59), (0.0, -0.02, 1.55), 115, (1200, 850)
    else:
        camera.location, target, camera.data.lens, size = (0.25, -0.72, 1.46), (0.025, -0.01, 1.42), 88, (1000, 1000)
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
results = []
for selected_family in range(5):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene; scene.frame_set(1)
    hair = bpy.data.objects[HAIR]; scalp = bpy.data.objects[SCALP]
    hair.hide_render = hair.hide_viewport = scalp.hide_render = scalp.hide_viewport = False
    attribute = hair.data.attributes[FAMILY]
    before_curves, before_points = len(hair.data.curves), len(hair.data.points)
    remove = [index for index in range(before_curves) if attribute.data[index].value != selected_family]
    hair.data.remove_curves(indices=remove)
    label = f"family-{selected_family}"
    renders = [render(scene, label, view) for view in ("front", "hairline", "right-temple")]
    results.append({"family": selected_family, "curves": len(hair.data.curves), "points": len(hair.data.points),
                    "removedCurves": len(remove), "sourceCurves": before_curves, "sourcePoints": before_points,
                    "renders": renders})

REPORT.write_text(json.dumps({
    "revision": "v249r1125-physical-family-isolation",
    "source": str(SOURCE),
    "method": "physically remove every non-selected curve before rendering each family; no radius masking",
    "diagnosticOnly": True,
    "websitePromotionApproved": False,
    "families": results,
}, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1125=" + json.dumps({"families": [{"family": r["family"], "curves": r["curves"], "points": r["points"]} for r in results]}))
