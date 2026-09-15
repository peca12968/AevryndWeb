"""Transfer the authored visible r420 lid margins into the current r1001 eye frame."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
GUIDE_SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
TARGET_SOURCE = ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1001.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-authored-lid-margin-transfer-r1013-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1013-authored-lid-margin-transfer.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1013-authored-lid-margin-transfer"


def object_bounds(names):
    points = []
    for name in names:
        obj = bpy.data.objects[name]
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return {"center": list((minimum + maximum) * 0.5), "radius": list((maximum - minimum) * 0.5)}


def curve_points(name):
    obj = bpy.data.objects[name]
    spline = obj.data.splines[0]
    if spline.type == "BEZIER":
        return [obj.matrix_world @ point.co for point in spline.bezier_points]
    return [obj.matrix_world @ point.co.xyz for point in spline.points]


def normalize(point, frame):
    center, radius = Vector(frame["center"]), Vector(frame["radius"])
    return [(point[axis] - center[axis]) / radius[axis] for axis in range(3)]


def denormalize(values, frame):
    center, radius = Vector(frame["center"]), Vector(frame["radius"])
    return Vector(tuple(center[axis] + values[axis] * radius[axis] for axis in range(3)))


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
    shader.inputs["Emission Strength"].default_value = 2.2
    shader.inputs["Roughness"].default_value = 0.28
    return mat


def make_curve(name, points, mat):
    curve = bpy.data.curves.new(name + "Geometry", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.00020
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for slot, point in zip(spline.points, points):
        slot.co = (*point, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj["aevrynd_role"] = "diagnostic_authored_lid_margin"
    obj["aevrynd_revision"] = "v249r1013"
    return obj


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(GUIDE_SOURCE))
guide_frames = {
    side: object_bounds((f"AevryndEye_{side}_ScleraOpen_R420", f"AevryndEye_{side}_CorneaConvex_R420"))
    for side in ("L", "R")
}
normalized = {}
for side in ("L", "R"):
    normalized[side] = {}
    for kind in ("Upper", "Lower"):
        points = curve_points(f"AevryndEye_{side}_{kind}LidMargin_R258")
        normalized[side][kind.lower()] = [normalize(point, guide_frames[side]) for point in points]

bpy.ops.wm.open_mainfile(filepath=str(TARGET_SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
target_frames = {
    side: object_bounds((f"Eye_{side}_Sclera", f"Eye_{side}_Cornea"))
    for side in ("L", "R")
}
materials = {
    "upper": make_material("Aevrynd_Diagnostic_UpperMargin_R1013", (0.04, 0.95, 0.82)),
    "lower": make_material("Aevrynd_Diagnostic_LowerMargin_R1013", (0.98, 0.20, 0.62)),
}
mapped = {}
objects = []
for side in ("L", "R"):
    mapped[side] = {}
    for kind in ("upper", "lower"):
        points = [denormalize(values, target_frames[side]) for values in normalized[side][kind]]
        # Offset only 0.20 mm toward the camera; the authored curves should
        # already describe the visible front margin rather than the rear hole.
        points = [Vector((point.x, point.y - 0.00020, point.z)) for point in points]
        mapped[side][kind] = [list(point) for point in points]
        objects.append(make_curve(f"Diagnostic_{side}_{kind.title()}LidMargin_R1013", points, materials[kind]))

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
rendered = []
for name, location, target in (
    ("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)),
    ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
    ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
):
    camera.location = location
    look_at(camera, target)
    path = RENDER_DIR / f"{name}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    rendered.append(str(path))

for name in hidden:
    bpy.data.objects[name].hide_render = False
scene["aevrynd_mainline_revision"] = "v249r1013-authored-lid-margin-transfer-study"
scene["aevrynd_mainline_parent"] = TARGET_SOURCE.name
scene["aevrynd_release_state"] = "DIAGNOSTIC_ONLY_NO_WEBSITE_PROMOTION"
report = {
    "guideSource": str(GUIDE_SOURCE),
    "targetSource": str(TARGET_SOURCE),
    "output": str(OUTPUT),
    "guideEyeFrames": guide_frames,
    "targetEyeFrames": target_frames,
    "normalizedGuideMargins": normalized,
    "mappedWorldMargins": mapped,
    "pointCounts": {side: {kind: len(points) for kind, points in values.items()} for side, values in mapped.items()},
    "layers": [obj.name for obj in objects],
    "rendered": rendered,
    "status": "VISUAL_ALIGNMENT_REVIEW_REQUIRED",
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1013_AUTHORED_LID_MARGIN_TRANSFER=" + json.dumps({
    "output": str(OUTPUT), "pointCounts": report["pointCounts"], "rendered": rendered, "status": report["status"]
}, sort_keys=True))
