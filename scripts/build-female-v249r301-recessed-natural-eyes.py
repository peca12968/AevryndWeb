import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-pruned-dynamic-outliers-r298.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-recessed-natural-eyes-r301.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r301-recessed-natural-eyes"
SCLERA_MATERIAL = "Aevrynd_EyeSclera_Physical_R252"
DEPTH = 0.0012
IRIS_SCALE = 1.08
EYE_OBJECTS = [
    f"AevryndEye_{side}_{part}"
    for side in ("L", "R")
    for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253")
]
IRIS_OBJECTS = [
    f"AevryndEye_{side}_{part}"
    for side in ("L", "R")
    for part in ("Limbal_R253", "Iris_R253", "Pupil_R253")
]


def bounds(obj):
    values = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return {axis: [min(point[index] for point in values), max(point[index] for point in values)] for index, axis in enumerate(("x", "y", "z"))}


def radial_extent(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    cx = (min(point.x for point in points) + max(point.x for point in points)) * 0.5
    cz = (min(point.z for point in points) + max(point.z for point in points)) * 0.5
    return {"centerXZ": [cx, cz], "maximumRadiusM": max(((point.x - cx) ** 2 + (point.z - cz) ** 2) ** 0.5 for point in points)}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, frame, name, location, target=(0.0, 0.0, 1.56), lens=82, size=1000):
    scene.frame_set(frame)
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
before = {name: bounds(bpy.data.objects[name]) for name in EYE_OBJECTS}
for name in EYE_OBJECTS:
    obj = bpy.data.objects[name]
    for vertex in obj.data.vertices:
        vertex.co.y += DEPTH
    obj.data.update()
    obj["aevrynd_revision"] = "v249r301"
    obj["aevrynd_recess_m"] = DEPTH
for name in IRIS_OBJECTS:
    obj = bpy.data.objects[name]
    center_x = sum(vertex.co.x for vertex in obj.data.vertices) / len(obj.data.vertices)
    center_z = sum(vertex.co.z for vertex in obj.data.vertices) / len(obj.data.vertices)
    for vertex in obj.data.vertices:
        vertex.co.x = center_x + (vertex.co.x - center_x) * IRIS_SCALE
        vertex.co.z = center_z + (vertex.co.z - center_z) * IRIS_SCALE
    obj.data.update()
    obj["aevrynd_iris_scale"] = IRIS_SCALE
material = bpy.data.materials[SCLERA_MATERIAL]
ramp = next(node for node in material.node_tree.nodes if node.type == "VALTORGB")
ramp.color_ramp.elements[0].color = (0.29, 0.235, 0.195, 1.0)
ramp.color_ramp.elements[1].color = (0.60, 0.535, 0.465, 1.0)
material["aevrynd_revision"] = "v249r301"
material["aevrynd_role"] = "warm low-luminance physical sclera"
after = {name: bounds(bpy.data.objects[name]) for name in EYE_OBJECTS}
stack = {}
failures = []
for side in ("L", "R"):
    cornea = radial_extent(bpy.data.objects[f"AevryndEye_{side}_Cornea_R252"])
    iris = radial_extent(bpy.data.objects[f"AevryndEye_{side}_Iris_R253"])
    pupil = radial_extent(bpy.data.objects[f"AevryndEye_{side}_Pupil_R253"])
    stack[side] = {"cornea": cornea, "iris": iris, "pupil": pupil, "irisWithinCornea": iris["maximumRadiusM"] <= cornea["maximumRadiusM"], "pupilWithinIris": pupil["maximumRadiusM"] <= iris["maximumRadiusM"]}
    if not stack[side]["irisWithinCornea"] or not stack[side]["pupilWithinIris"]:
        failures.append({"side": side, "stack": stack[side]})
scene["aevrynd_mainline_revision"] = "v249r301-recessed-natural-eyes"
scene["aevrynd_release_state"] = "EYE_BINDING_AND_VISUAL_REVIEW_PENDING" if not failures else "EYE_STACK_FAIL"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in ((1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)), (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)), (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59))):
    render(camera, frame, name, location)
render(camera, 1, "face-close-f01", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92, 1000)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "eyeRecessM": DEPTH,
    "irisScale": IRIS_SCALE, "scleraRamp": [[0.29, 0.235, 0.195, 1.0], [0.60, 0.535, 0.465, 1.0]],
    "beforeBounds": before, "afterBounds": after, "stackAudit": stack,
    "failures": failures, "ownedAssetOnly": True, "renderDirectory": str(RENDER_DIR),
    "status": "BINDING_AND_VISUAL_REVIEW_PENDING" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R301_RECESSED_NATURAL_EYES=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
