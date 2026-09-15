"""Render the r446 open eyelid loops mapped into the current r1001 eye frame."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1001.blend"
MAPPING = ASSETS / "female-v249-mainline-r1011-open-eyelid-loop-transfer.json"
OUTPUT = ASSETS / "aevrynd-female-cc0-open-eyelid-loop-map-r1012-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1012-open-eyelid-loop-map.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1012-open-eyelid-loop-map"
VIEWS = (
    ("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)),
    ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
    ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
)


def material(name, color):
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1.0)
    value.use_nodes = True
    value.node_tree.nodes.clear()
    principled = value.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    output = value.node_tree.nodes.new("ShaderNodeOutputMaterial")
    value.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    principled.inputs["Base Color"].default_value = (*color, 1.0)
    principled.inputs["Roughness"].default_value = 0.32
    principled.inputs["Emission Color"].default_value = (*color, 1.0)
    principled.inputs["Emission Strength"].default_value = 1.8
    return value


def curve_loop(name, points, mat):
    curve = bpy.data.curves.new(name + "Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.00018
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for slot, point in zip(spline.points, points):
        # Move 1.2 mm toward the review camera so the diagnostic line stays
        # visible over the current closed socket surface.
        slot.co = (point[0], point[1] - 0.00120, point[2], 1.0)
    spline.use_cyclic_u = True
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj["aevrynd_role"] = "diagnostic_open_eyelid_loop"
    obj["aevrynd_source"] = "r446 open boundary normalized into r1001 eye frame"
    obj["aevrynd_revision"] = "v249r1012"
    return obj


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
left = material("Aevrynd_Diagnostic_OpenLoop_L_R1012", (0.05, 0.95, 0.85))
right = material("Aevrynd_Diagnostic_OpenLoop_R_R1012", (0.95, 0.25, 0.75))
objects = []
for side, mat in (("L", left), ("R", right)):
    points = mapping["targetMapping"][side]["mappedWorldCoordinates"]
    objects.append(curve_loop(f"Diagnostic_OpenEyelidLoop_{side}_R1012", points, mat))

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
for name, location, target in VIEWS:
    camera.location = location
    look_at(camera, target)
    path = RENDER_DIR / f"{name}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    rendered.append(str(path))

for name in hidden:
    bpy.data.objects[name].hide_render = False
scene["aevrynd_mainline_revision"] = "v249r1012-open-eyelid-loop-map-study"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "DIAGNOSTIC_ONLY_NO_WEBSITE_PROMOTION"
report = {
    "source": str(SOURCE),
    "mapping": str(MAPPING),
    "output": str(OUTPUT),
    "layers": [obj.name for obj in objects],
    "loopVerticesPerEye": {side: mapping["openLoops"][side]["vertexCount"] for side in ("L", "R")},
    "mappingDistanceM": {side: mapping["targetMapping"][side]["distanceM"] for side in ("L", "R")},
    "rendered": rendered,
    "status": "VISUAL_ALIGNMENT_REVIEW_REQUIRED",
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1012_OPEN_EYELID_LOOP_MAP=" + json.dumps(report, sort_keys=True))
