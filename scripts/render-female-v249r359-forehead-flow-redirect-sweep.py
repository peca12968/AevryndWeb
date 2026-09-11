import json
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-forehead-flow-redirect-r359.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r359-forehead-flow-redirect-sweep"
HAIR_NAMES = ("AevryndFemalePrimaryClumps_R264", "AevryndFemaleSecondaryFill_R264")
ROI = (0.45, 0.78, 0.66, 0.86)
VARIANTS = (
    ("a-current", 0.000),
    ("b-redirect-10mm", 0.010),
    ("c-redirect-20mm", 0.020),
    ("d-redirect-30mm", 0.030),
)


def smoothstep(a, b, value):
    t = max(0.0, min(1.0, (value - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.image_settings.file_format = "PNG"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
for name in ("Aevrynd R249 Key", "Aevrynd R249 Fill", "Aevrynd R249 Rim"):
    bpy.data.objects[name].data.energy *= 1.35

camera = bpy.data.objects["Aevrynd R249 Review Camera"]
camera.location = (0.0, -0.68, 1.605)
camera.data.lens = 92
look_at(camera, (0.0, -0.035, 1.606))
bpy.context.view_layer.update()

x_min, x_max, y_min, y_max = ROI
families = {}
for name in HAIR_NAMES:
    hair = bpy.data.objects[name]
    hair.data = hair.data.copy()
    original = [point.position.copy() for point in hair.data.points]
    selected = []
    for curve_index, curve in enumerate(hair.data.curves):
        hits = 0
        for index in range(curve.first_point_index + 3, curve.first_point_index + curve.points_length):
            world = hair.matrix_world @ hair.data.points[index].position
            ndc = world_to_camera_view(scene, camera, world)
            if ndc.z > 0.0 and x_min < ndc.x < x_max and y_min < ndc.y < y_max and world.y < 0.02:
                hits += 1
        if hits >= 2:
            selected.append(curve_index)
    families[name] = {"object": hair, "original": original, "selected": selected}

views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("hairline-high", (0.0, -0.57, 1.76), (0.0, -0.02, 1.64), 92),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
    ("back", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
)
metrics = {}

for label, redirect_m in VARIANTS:
    family_metrics = {}
    for name, record in families.items():
        hair = record["object"]
        for index, position in enumerate(record["original"]):
            hair.data.points[index].position = position
        maximum = 0.0
        if redirect_m:
            for curve_index in record["selected"]:
                curve = hair.data.curves[curve_index]
                for offset in range(3, curve.points_length):
                    point_index = curve.first_point_index + offset
                    t = offset / max(1, curve.points_length - 1)
                    displacement = redirect_m * smoothstep(0.10, 0.58, t)
                    point = record["original"][point_index].copy()
                    point.x += displacement
                    hair.data.points[point_index].position = point
                    maximum = max(maximum, displacement)
        family_metrics[name] = {
            "selectedCurves": len(record["selected"]),
            "maximumLateralRedirectM": maximum,
            "curveCountUnchanged": len(hair.data.curves),
        }
    bpy.context.view_layer.update()
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    metrics[label] = {"redirectM": redirect_m, "families": family_metrics}

report = {
    "source": str(SOURCE),
    "renderDirectory": str(RENDER_DIR),
    "method": "Select front-right curves through the corrected forehead ROI and ease their non-root points laterally toward the right temple without deleting geometry.",
    "cameraSpaceRoi": ROI,
    "reviewLightCalibration": "r351 selected 1.35x r345 energies",
    "variants": metrics,
    "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R359_FOREHEAD_FLOW_REDIRECT=" + json.dumps(report, sort_keys=True))
