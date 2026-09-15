import json
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-retargeted-rig-r603.blend"
REVISION = os.environ.get("AEVRYND_SHOULDER_REVISION", "r614")
COMPRESSION = float(os.environ.get("AEVRYND_SHOULDER_COMPRESSION", "0.08"))
OUTPUT = ASSETS / f"aevrynd-female-cc0-shoulder-corrective-shapekeys-{REVISION}.blend"
REPORT = ASSETS / f"female-v249-mainline-cc0-shoulder-corrective-shapekeys-{REVISION}.build.json"
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
    variable.targets[0].data_path = f'pose.bones["upper_arm.{side}"].rotation_quaternion[3]'
    direction = "-q" if side == "L" else "q"
    driver.expression = f"max(0,min(1,(({direction})-0.03)/0.268))"
    return driver.expression


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
visible = body.vertex_groups["body"]
# Select the source cage by its evaluated neutral position. The retargeted armature
# already moves the MPFB cage at frame 1, so basis coordinates do not line up with
# the strict audit's neutral-space shoulder coordinates.
temporarily_hidden = []
for modifier in body.modifiers:
    if modifier.type in {"MASK", "SUBSURF"} and modifier.show_viewport:
        modifier.show_viewport = False
        temporarily_hidden.append(modifier)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
evaluated_mesh = evaluated.to_mesh()
if len(evaluated_mesh.vertices) != len(body.data.vertices):
    raise RuntimeError(
        f"neutral cage topology mismatch: {len(evaluated_mesh.vertices)} != {len(body.data.vertices)}"
    )
neutral_cage = [evaluated.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices]
evaluated.to_mesh_clear()
for modifier in temporarily_hidden:
    modifier.show_viewport = True
bpy.context.view_layer.update()
created = {}
for side, sign in (("L", 1.0), ("R", -1.0)):
    key = body.shape_key_add(name=f"ShoulderRaise90.{side}", from_mix=False)
    key.relative_key = body.data.shape_keys.key_blocks["Basis"]
    changed = 0
    maximum_delta = 0.0
    center = 0.1465
    for vertex in body.data.vertices:
        try:
            if visible.weight(vertex.index) <= 0.0:
                continue
        except RuntimeError:
            continue
        point = neutral_cage[vertex.index]
        lateral = point.x * sign
        if not (0.112 <= lateral <= 0.188 and -0.082 <= point.y <= 0.042 and 1.108 <= point.z <= 1.238):
            continue
        edge = min(
            (lateral - 0.112) / 0.022,
            (0.188 - lateral) / 0.022,
            (point.y + 0.082) / 0.035,
            (0.042 - point.y) / 0.035,
            (point.z - 1.108) / 0.035,
            (1.238 - point.z) / 0.035,
        )
        weight = smoothstep(edge)
        if weight <= 0.0:
            continue
        delta_lateral = -COMPRESSION * (lateral - center) * weight
        key.data[vertex.index].co.x += sign * delta_lateral
        changed += 1
        maximum_delta = max(maximum_delta, abs(delta_lateral))
    expression = add_driver(key, side)
    created[side] = {
        "vertices": changed,
        "maximumBasisDeltaM": maximum_delta,
        "driver": expression,
    }

scene.frame_set(20)
bpy.context.view_layer.update()
evaluated_values = {
    side: body.data.shape_keys.key_blocks[f"ShoulderRaise90.{side}"].value
    for side in ("L", "R")
}
scene.frame_set(1)
body["aevrynd_revision"] = f"v249{REVISION}"
body["aevrynd_shoulder_corrective"] = "bilateral quaternion-driven shoulder compression shape keys"
scene["aevrynd_mainline_revision"] = f"v249{REVISION}-cc0-shoulder-corrective-shapekeys"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "DEFORMATION_AND_DYNAMIC_COLLISION_AUDIT_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "revision": REVISION,
    "compression": COMPRESSION,
    "created": created,
    "evaluatedValuesAtFrame20": evaluated_values,
    "shapeKeys": len(body.data.shape_keys.key_blocks),
    "status": "DEFORMATION_AND_DYNAMIC_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_SHOULDER_CORRECTIVE_SHAPEKEYS=" + json.dumps(report, sort_keys=True))
