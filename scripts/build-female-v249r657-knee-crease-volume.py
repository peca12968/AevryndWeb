import json
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = Path(os.environ.get(
    "AEVRYND_KNEE_VOLUME_SOURCE",
    ASSETS / "aevrynd-female-cc0-elbow-crease-volume-r655.blend",
))
REVISION = os.environ.get("AEVRYND_KNEE_VOLUME_REVISION", "r657")
VERTICAL_EXPANSION = float(os.environ.get("AEVRYND_KNEE_VOLUME_VERTICAL", "2.0"))
LATERAL_EXPANSION = float(os.environ.get("AEVRYND_KNEE_VOLUME_LATERAL", "0.0"))
DEPTH_EXPANSION = float(os.environ.get("AEVRYND_KNEE_VOLUME_DEPTH", "0.0"))
CORE_RADIUS = float(os.environ.get("AEVRYND_KNEE_VOLUME_CORE", "0.008"))
OUTER_RADIUS = float(os.environ.get("AEVRYND_KNEE_VOLUME_RADIUS", "0.045"))
CENTER_X = float(os.environ.get("AEVRYND_KNEE_VOLUME_CENTER_X", "0.1670"))
CENTER_Y = float(os.environ.get("AEVRYND_KNEE_VOLUME_CENTER_Y", "-0.0160"))
CENTER_Z = float(os.environ.get("AEVRYND_KNEE_VOLUME_CENTER_Z", "0.4485"))
DRIVER_ONSET_Q = float(os.environ.get("AEVRYND_KNEE_VOLUME_ONSET_Q", "0.03"))
DRIVER_FULL_Q = float(os.environ.get("AEVRYND_KNEE_VOLUME_FULL_Q", "0.609"))
OUTPUT = ASSETS / f"aevrynd-female-cc0-knee-crease-volume-{REVISION}.blend"
REPORT = ASSETS / f"female-v249-mainline-cc0-knee-crease-volume-{REVISION}.build.json"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def add_driver(key, side):
    curve = key.driver_add("value")
    driver = curve.driver
    driver.type = "SCRIPTED"
    variable = driver.variables.new()
    variable.name = "q"
    variable.type = "SINGLE_PROP"
    variable.targets[0].id_type = "OBJECT"
    variable.targets[0].id = bpy.data.objects[RIG]
    variable.targets[0].data_path = f'pose.bones["shin.{side}"].rotation_quaternion[1]'
    driver.expression = f"max(0,min(1,(q-{DRIVER_ONSET_Q:.9f})/{DRIVER_FULL_Q - DRIVER_ONSET_Q:.9f}))"
    return driver.expression


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
visible = body.vertex_groups["body"]
hidden = []
for modifier in body.modifiers:
    if modifier.type in {"MASK", "SUBSURF"} and modifier.show_viewport:
        modifier.show_viewport = False
        hidden.append(modifier)
bpy.context.view_layer.update()
evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
if len(mesh.vertices) != len(body.data.vertices):
    raise RuntimeError(f"neutral cage topology mismatch: {len(mesh.vertices)} != {len(body.data.vertices)}")
neutral = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
evaluated.to_mesh_clear()
for modifier in hidden:
    modifier.show_viewport = True
bpy.context.view_layer.update()

basis = body.data.shape_keys.key_blocks["Basis"]
created = {}
for side, sign in (("L", 1.0), ("R", -1.0)):
    center = Vector((sign * CENTER_X, CENTER_Y, CENTER_Z))
    key = body.shape_key_add(name=f"KneeCreaseVolume75.{side}", from_mix=False)
    key.relative_key = basis
    changed = 0
    maximum_delta = 0.0
    for index, point in enumerate(neutral):
        try:
            if visible.weight(index) <= 0.0:
                continue
        except RuntimeError:
            continue
        delta = point - center
        distance = delta.length
        if distance >= OUTER_RADIUS:
            continue
        if distance <= CORE_RADIUS:
            weight = 1.0
        else:
            weight = smoothstep((OUTER_RADIUS - distance) / (OUTER_RADIUS - CORE_RADIUS))
        dx = LATERAL_EXPANSION * (point.x - center.x) * weight
        dy = DEPTH_EXPANSION * (point.y - center.y) * weight
        dz = VERTICAL_EXPANSION * (point.z - center.z) * weight
        key.data[index].co = basis.data[index].co + Vector((dx, dy, dz))
        changed += 1
        maximum_delta = max(maximum_delta, (dx * dx + dy * dy + dz * dz) ** 0.5)
    created[side] = {
        "vertices": changed,
        "maximumBasisDeltaM": maximum_delta,
        "driver": add_driver(key, side),
    }

body["aevrynd_revision"] = f"v249{REVISION}"
body["aevrynd_knee_crease_volume"] = "bilateral compact vertical crease-volume expansion driven by knee flexion"
scene["aevrynd_mainline_revision"] = f"v249{REVISION}-cc0-knee-crease-volume"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "FULL_JOINT_DEFORMATION_AND_COLLISION_AUDIT_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "revision": REVISION,
    "verticalExpansion": VERTICAL_EXPANSION, "coreRadiusM": CORE_RADIUS,
    "lateralExpansion": LATERAL_EXPANSION, "depthExpansion": DEPTH_EXPANSION,
    "centerM": [CENTER_X, CENTER_Y, CENTER_Z],
    "driver": {"onsetQ": DRIVER_ONSET_Q, "fullQ": DRIVER_FULL_Q},
    "outerRadiusM": OUTER_RADIUS, "created": created,
    "shapeKeys": len(body.data.shape_keys.key_blocks),
    "status": "FULL_JOINT_DEFORMATION_AND_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_KNEE_CREASE_VOLUME=" + json.dumps(report, sort_keys=True))
