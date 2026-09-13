import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-runtime-brows-r480.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-smoothed-lip-margin-r481.blend"
REPORT = ASSETS / "female-v249-mainline-smoothed-lip-margin-r481.build-report.json"
REVIEW = ASSETS / "reviews/v249r481-smoothed-lip-margin"
UPPER = "Lip_Upper"
STRENGTH = 1.0


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def gaussian(values, sigma=1.65, radius=4):
    result = []
    for index in range(len(values)):
        total = 0.0
        weight_sum = 0.0
        for offset in range(-radius, radius + 1):
            sample = max(0, min(len(values) - 1, index + offset))
            weight = math.exp(-0.5 * (offset / sigma) ** 2)
            total += values[sample] * weight
            weight_sum += weight
        result.append(total / weight_sum)
    return result


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, frame, name, location, target, lens, size):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(REVIEW / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
upper = bpy.data.objects[UPPER]
mesh = upper.data
if len(mesh.vertices) != 325 or len(mesh.polygons) != 256:
    raise RuntimeError("unexpected r480 upper-lip topology; expected a 65x5 grid")
for polygon in mesh.polygons:
    expected_material = 2 if polygon.index % 4 == 3 else 1
    if polygon.material_index != expected_material:
        raise RuntimeError("unexpected upper-lip material-band topology")

original = [[mesh.vertices[column * 5 + row].co.copy() for row in range(5)] for column in range(65)]
changed = []
row_moves = {"innerShoulder": [], "innerMargin": []}
for row, smoothing_weight, label in ((3, 0.55, "innerShoulder"), (4, 0.92, "innerMargin")):
    smooth_y = gaussian([original[column][row].y for column in range(65)])
    smooth_z = gaussian([original[column][row].z for column in range(65)])
    for column in range(65):
        u = (column - 32) / 32.0
        interior = smoothstep((1.0 - abs(u)) / 0.14)
        weight = min(1.0, STRENGTH * smoothing_weight * interior)
        vertex = mesh.vertices[column * 5 + row]
        before = vertex.co.copy()
        vertex.co.y += (smooth_y[column] - vertex.co.y) * weight
        vertex.co.z += (smooth_z[column] - vertex.co.z) * weight
        if row == 4:
            central_drop = -0.00022 * math.exp(-0.5 * (u / 0.155) ** 2)
            side_lift = 0.000055 * math.exp(-0.5 * ((abs(u) - 0.36) / 0.13) ** 2)
            vertex.co.z += STRENGTH * interior * (central_drop + side_lift)
            corner = smoothstep((abs(u) - 0.70) / 0.25) * STRENGTH
            neighbor = mesh.vertices[column * 5 + 3].co
            vertex.co.y += (neighbor.y - vertex.co.y) * corner
            vertex.co.z += (neighbor.z - vertex.co.z) * corner
        delta = (vertex.co - before).length
        row_moves[label].append(delta * 1000.0)
        if delta > 1e-9:
            changed.append(vertex.index)

mesh.update()
upper["aevrynd_lip_margin_method"] = "65-column Gaussian fairing; restrained central tubercle; commissure closure"
upper["aevrynd_lip_margin_strength"] = STRENGTH
upper["aevrynd_revision"] = "v249r481"
scene["aevrynd_mainline_revision"] = "v249r481-smoothed-lip-margin"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "LIP_MARGIN_VISUAL_REVIEW_PENDING"

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
REVIEW.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
views = (
    (1, "01-face-front-f01", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100)),
    (1, "02-mouth-close-f01", (0.0, -0.405, 1.528), (0.0, -0.115, 1.528), 135, (1400, 800)),
    (1, "03-mouth-oblique-f01", (0.235, -0.405, 1.53), (0.0, -0.112, 1.528), 135, (1400, 800)),
    (20, "04-face-front-f20", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100)),
    (20, "05-mouth-close-f20", (0.0, -0.405, 1.528), (0.0, -0.115, 1.528), 135, (1400, 800)),
)
for view in views:
    render(scene, camera, *view)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": upper["aevrynd_lip_margin_method"],
    "strength": STRENGTH,
    "topology": {"vertices": len(mesh.vertices), "polygons": len(mesh.polygons), "columns": 65, "rows": 5},
    "changedVertexCount": len(set(changed)),
    "maximumMoveMm": max(max(values) for values in row_moves.values()),
    "meanMoveMmByRow": {name: sum(values) / len(values) for name, values in row_moves.items()},
    "geometryChangedOutsideUpperLip": False,
    "materialsChanged": False,
    "reviewLightingChanged": False,
    "reviewDirectory": str(REVIEW),
    "status": "TECHNICAL_CANDIDATE_VISUAL_COLLISION_TONE_AUDITS_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R481_SMOOTHED_LIP_MARGIN=" + json.dumps(report, sort_keys=True))
