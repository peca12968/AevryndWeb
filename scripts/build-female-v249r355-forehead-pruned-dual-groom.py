import json
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-forehead-pruned-dual-groom-r355.blend"
REPORT = ASSETS / "female-v249-mainline-forehead-pruned-dual-groom-r355.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r355-forehead-pruned-dual-groom"
HAIR_NAMES = ("AevryndFemalePrimaryClumps_R264", "AevryndFemaleSecondaryFill_R264")
ROI = (0.26, 0.79, 0.36, 0.60)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def subset_hair(source, keep, suffix):
    data = bpy.data.hair_curves.new(f"{source.name}_{suffix}")
    data.add_curves([source.curves[index].points_length for index in keep])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    family = data.attributes.new("aevrynd_guide_family", "INT", "CURVE")
    source_radius = source.attributes["radius"].data
    source_family = source.attributes["aevrynd_guide_family"].data
    for destination_curve_index, source_curve_index in enumerate(keep):
        source_curve = source.curves[source_curve_index]
        destination_curve = data.curves[destination_curve_index]
        family.data[destination_curve_index].value = source_family[source_curve_index].value
        for offset in range(source_curve.points_length):
            source_point_index = source_curve.first_point_index + offset
            destination_point_index = destination_curve.first_point_index + offset
            data.points[destination_point_index].position = source.points[source_point_index].position
            radius.data[destination_point_index].value = source_radius[source_point_index].value
    for material in source.materials:
        data.materials.append(material)
    return data


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
camera.location = (0.0, -0.68, 1.605)
camera.data.lens = 92
look_at(camera, (0.0, -0.035, 1.606))
bpy.context.view_layer.update()

x_min, x_max, y_min, y_max = ROI
metrics = {}
for name in HAIR_NAMES:
    hair = bpy.data.objects[name]
    source = hair.data
    keep = []
    for curve_index, curve in enumerate(source.curves):
        hits = 0
        for index in range(curve.first_point_index + 3, curve.first_point_index + curve.points_length):
            world = hair.matrix_world @ source.points[index].position
            ndc = world_to_camera_view(scene, camera, world)
            if ndc.z > 0.0 and x_min < ndc.x < x_max and y_min < ndc.y < y_max:
                hits += 1
        if hits < 2:
            keep.append(curve_index)
    original_curves = len(source.curves)
    original_points = len(source.points)
    hair.data = subset_hair(source, keep, "R355")
    hair["aevrynd_revision"] = "v249r355"
    hair["aevrynd_curve_count"] = len(keep)
    hair["aevrynd_forehead_prune_method"] = "front camera-space ROI, two or more non-root points"
    hair["aevrynd_forehead_prune_roi"] = list(ROI)
    metrics[name] = {
        "originalCurves": original_curves,
        "retainedCurves": len(keep),
        "removedCurves": original_curves - len(keep),
        "originalPoints": original_points,
        "retainedPoints": len(hair.data.points),
        "removedPoints": original_points - len(hair.data.points),
    }

# Store the accepted r351 review calibration in this authoring file.
light_energies = {}
for name in ("Aevrynd R249 Key", "Aevrynd R249 Fill", "Aevrynd R249 Rim"):
    bpy.data.objects[name].data.energy *= 1.35
    light_energies[name] = bpy.data.objects[name].data.energy

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.image_settings.file_format = "PNG"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
views = (
    (1, "front-f01", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (20, "front-f20", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "face-close-f01", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    (1, "eyes-close-f01", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105),
    (1, "three-quarter-f01", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
    (1, "left-f01", (-0.72, -0.55, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "right-f01", (0.72, -0.55, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "back-f01", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
)
for frame, label, location, target, lens in views:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r355-forehead-pruned-dual-groom"
scene["aevrynd_release_state"] = "TECHNICAL_AUDITS_PENDING_VISUAL_FAIL"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "selectedFrom": "r354 c-mid-forehead",
    "cameraSpaceRoi": ROI,
    "minimumNonRootPointsInRoiForRemoval": 2,
    "hairGeometry": metrics,
    "reviewLightEnergyW": light_energies,
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "status": "TECHNICAL_AUDITS_PENDING_VISUAL_FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R355_FOREHEAD_PRUNED_DUAL_GROOM=" + json.dumps(report, sort_keys=True))
