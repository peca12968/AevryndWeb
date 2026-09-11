import json
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-dual-family-forehead-filter-r353.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r353-dual-family-forehead-filter-sweep"
HAIR_NAMES = ("AevryndFemalePrimaryClumps_R264", "AevryndFemaleSecondaryFill_R264")
VARIANTS = (
    ("a-current", None),
    ("b-low-forehead", (0.26, 0.79, 0.36, 0.53)),
    ("c-mid-forehead", (0.26, 0.79, 0.36, 0.60)),
    ("d-broad-forehead", (0.24, 0.81, 0.34, 0.66)),
)


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

families = {}
for name in HAIR_NAMES:
    hair = bpy.data.objects[name]
    hair.data = hair.data.copy()
    radius = hair.data.attributes["radius"].data
    projected = []
    for curve in hair.data.curves:
        points = []
        start = curve.first_point_index
        for index in range(start + 3, start + curve.points_length):
            world = hair.matrix_world @ hair.data.points[index].position
            ndc = world_to_camera_view(scene, camera, world)
            points.append((ndc.x, ndc.y, ndc.z))
        projected.append(points)
    families[name] = {
        "object": hair,
        "radius": radius,
        "original": [value.value for value in radius],
        "projected": projected,
    }

views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("hairline-high", (0.0, -0.57, 1.76), (0.0, -0.02, 1.64), 92),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
)
metrics = {}

for label, roi in VARIANTS:
    variant_metrics = {}
    for name, family in families.items():
        hair = family["object"]
        radius = family["radius"]
        for index, value in enumerate(family["original"]):
            radius[index].value = value
        flagged = []
        if roi is not None:
            x_min, x_max, y_min, y_max = roi
            for curve_index, points in enumerate(family["projected"]):
                hits = sum(
                    1
                    for x, y, depth in points
                    if depth > 0.0 and x_min < x < x_max and y_min < y < y_max
                )
                if hits >= 2:
                    flagged.append(curve_index)
                    curve = hair.data.curves[curve_index]
                    for index in range(curve.first_point_index, curve.first_point_index + curve.points_length):
                        radius[index].value = 0.0
        variant_metrics[name] = {
            "suppressedCurves": len(flagged),
            "retainedCurves": len(hair.data.curves) - len(flagged),
            "suppressedPoints": sum(hair.data.curves[index].points_length for index in flagged),
        }
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    metrics[label] = {"cameraSpaceRoi": roi, "families": variant_metrics}

report = {
    "source": str(SOURCE),
    "renderDirectory": str(RENDER_DIR),
    "method": "Apply the same camera-space forehead rejection to PrimaryClumps and SecondaryFill so redundant guide families cannot preserve the artifact.",
    "reviewLightCalibration": "r351 selected 1.35x r345 energies",
    "variants": metrics,
    "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R353_DUAL_FAMILY_FOREHEAD_FILTER=" + json.dumps(report, sort_keys=True))
