import json
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-extended-depth-forehead-prune-r357.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r357-extended-depth-forehead-prune-sweep"
HAIR_NAMES = ("AevryndFemalePrimaryClumps_R264", "AevryndFemaleSecondaryFill_R264")
ROI = (0.26, 0.79, 0.36, 0.60)
VARIANTS = (
    ("a-current", None),
    ("b-front-y-minus-0p04", -0.04),
    ("c-front-y-minus-0p02", -0.02),
    ("d-front-y-zero", 0.00),
    ("e-front-y-plus-0p02", 0.02),
)


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
    projected = []
    for curve in hair.data.curves:
        points = []
        for index in range(curve.first_point_index + 3, curve.first_point_index + curve.points_length):
            world = hair.matrix_world @ hair.data.points[index].position
            ndc = world_to_camera_view(scene, camera, world)
            points.append((ndc.x, ndc.y, ndc.z, world.y))
        projected.append(points)
    families[name] = {"object": hair, "source": hair.data, "projected": projected}

views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("hairline-high", (0.0, -0.57, 1.76), (0.0, -0.02, 1.64), 92),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
    ("back", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
)
metrics = {}

for label, front_y_limit in VARIANTS:
    variant_metrics = {}
    for name, record in families.items():
        source = record["source"]
        if front_y_limit is None:
            keep = list(range(len(source.curves)))
            record["object"].data = source
        else:
            keep = []
            for curve_index, points in enumerate(record["projected"]):
                hits = sum(
                    1
                    for x, y, depth, world_y in points
                    if depth > 0.0
                    and x_min < x < x_max
                    and y_min < y < y_max
                    and world_y < front_y_limit
                )
                if hits < 2:
                    keep.append(curve_index)
            record["object"].data = subset_hair(source, keep, label)
        variant_metrics[name] = {
            "retainedCurves": len(keep),
            "removedCurves": len(source.curves) - len(keep),
            "retainedPoints": sum(source.curves[index].points_length for index in keep),
        }
    bpy.context.view_layer.update()
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    metrics[label] = {
        "cameraSpaceRoi": ROI if front_y_limit is not None else None,
        "frontWorldYLimitM": front_y_limit,
        "families": variant_metrics,
    }

report = {
    "source": str(SOURCE),
    "renderDirectory": str(RENDER_DIR),
    "method": "Rebuild both groom families using the forehead screen ROI plus a front-world-Y guard so occluded rear curves are retained.",
    "reviewLightCalibration": "r351 selected 1.35x r345 energies",
    "variants": metrics,
    "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R357_EXTENDED_DEPTH_FOREHEAD_PRUNE=" + json.dumps(report, sort_keys=True))

