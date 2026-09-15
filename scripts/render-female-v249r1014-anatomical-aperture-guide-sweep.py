"""Sweep closed anatomical eyelid-aperture guides on the current r1001 face."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1001.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-anatomical-aperture-guides-r1014-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1014-anatomical-aperture-guide-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1014-anatomical-aperture-guide-sweep"
VARIANTS = (
    ("a-restrained", 0.34, 0.22),
    ("b-balanced", 0.40, 0.26),
    ("c-open", 0.48, 0.31),
)


def object_bounds(names):
    points = []
    for name in names:
        obj = bpy.data.objects[name]
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return (minimum + maximum) * 0.5, (maximum - minimum) * 0.5


def make_material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    shader = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    mat.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Emission Color"].default_value = (*color, 1.0)
    shader.inputs["Emission Strength"].default_value = 2.0
    shader.inputs["Roughness"].default_value = 0.30
    return mat


def guide_points(center, radius, side, upper_height, lower_depth):
    temple_sign = 1.0 if side == "L" else -1.0
    upper, lower = [], []
    extent = 0.88
    for index in range(41):
        u = -extent + 2.0 * extent * index / 40.0
        temporal = u * temple_sign
        arc = math.sqrt(max(0.0, 1.0 - (u / extent) ** 2))
        # Medial corner sits slightly lower; lateral corner rises gently.
        canthus_z = -0.035 + (temporal + extent) / (2.0 * extent) * 0.145
        for points, z_normalized in (
            (upper, canthus_z + upper_height * arc),
            (lower, canthus_z - lower_depth * arc),
        ):
            sphere = math.sqrt(max(0.04, 1.0 - u * u - min(0.82, abs(z_normalized)) ** 2))
            y = center.y - radius.y * sphere - 0.00028
            points.append(Vector((center.x + radius.x * u, y, center.z + radius.z * z_normalized)))
    return upper, lower


def make_curve(name, points, mat):
    curve = bpy.data.curves.new(name + "Geometry", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.00018
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for slot, point in zip(spline.points, points):
        slot.co = (*point, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj["aevrynd_role"] = "diagnostic_anatomical_aperture_guide"
    obj["aevrynd_revision"] = "v249r1014"
    return obj


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
frames = {side: object_bounds((f"Eye_{side}_Sclera", f"Eye_{side}_Cornea")) for side in ("L", "R")}
upper_mat = make_material("Aevrynd_Diagnostic_Upper_R1014", (0.04, 0.95, 0.82))
lower_mat = make_material("Aevrynd_Diagnostic_Lower_R1014", (0.98, 0.20, 0.62))

hidden = []
for obj in scene.objects:
    is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
    is_lash = obj.name.endswith(("UpperLashes", "LowerLashes"))
    if (is_hair or is_lash) and not obj.hide_render:
        obj.hide_render = True
        hidden.append(obj.name)

RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = scene.camera
camera.data.lens = 105
results = []
variant_objects = []
for label, upper_height, lower_depth in VARIANTS:
    for old in variant_objects:
        bpy.data.objects.remove(old, do_unlink=True)
    variant_objects = []
    measurements = {}
    for side in ("L", "R"):
        center, radius = frames[side]
        upper, lower = guide_points(center, radius, side, upper_height, lower_depth)
        variant_objects.append(make_curve(f"Diagnostic_{side}_Upper_{label}_R1014", upper, upper_mat))
        variant_objects.append(make_curve(f"Diagnostic_{side}_Lower_{label}_R1014", lower, lower_mat))
        measurements[side] = {
            "upperPoints": [list(point) for point in upper],
            "lowerPoints": [list(point) for point in lower],
            "medialClosureM": (upper[0 if side == "L" else -1] - lower[0 if side == "L" else -1]).length,
            "lateralClosureM": (upper[-1 if side == "L" else 0] - lower[-1 if side == "L" else 0]).length,
            "centralApertureM": max(point.z for point in upper) - min(point.z for point in lower),
        }
    rendered = []
    for view, location, target in (
        ("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)),
        ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
        ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
    ):
        camera.location = location
        look_at(camera, target)
        path = RENDER_DIR / f"{label}-{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(path))
    results.append({
        "label": label,
        "upperNormalizedHeight": upper_height,
        "lowerNormalizedDepth": lower_depth,
        "measurements": measurements,
        "rendered": rendered,
    })

for name in hidden:
    bpy.data.objects[name].hide_render = False
scene["aevrynd_mainline_revision"] = "v249r1014-anatomical-aperture-guide-study"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "DIAGNOSTIC_ONLY_NO_WEBSITE_PROMOTION"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "Aevrynd-authored closed almond guide in the current eye ellipsoid frame; lateral canthus is higher than medial and both margins share exact endpoints.",
    "eyeFrames": {side: {"center": list(value[0]), "radius": list(value[1])} for side, value in frames.items()},
    "variants": results,
    "selectedVariant": None,
    "status": "VISUAL_GUIDE_REVIEW_REQUIRED",
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1014_ANATOMICAL_APERTURE_GUIDES=" + json.dumps({
    "output": str(OUTPUT), "variants": [item["label"] for item in results], "status": report["status"]
}, sort_keys=True))
