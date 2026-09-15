import json
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-high-raise-correctives-r628.blend"
REVISION = os.environ.get("AEVRYND_TWIST_CORRECTIVE_REVISION", "r630")
LATERAL_COMPRESSION = float(os.environ.get("AEVRYND_TWIST_CORRECTIVE_LATERAL", "0.40"))
VERTICAL_COMPRESSION = float(os.environ.get("AEVRYND_TWIST_CORRECTIVE_VERTICAL", "0.30"))
OUTPUT = ASSETS / f"aevrynd-female-cc0-twist-raise-interaction-{REVISION}.blend"
REPORT = ASSETS / f"female-v249-mainline-cc0-twist-raise-interaction-{REVISION}.build.json"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
visible = body.vertex_groups["body"]

temporarily_hidden = []
for modifier in body.modifiers:
    if modifier.type in {"MASK", "SUBSURF"} and modifier.show_viewport:
        modifier.show_viewport = False
        temporarily_hidden.append(modifier)
bpy.context.view_layer.update()
evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
if len(mesh.vertices) != len(body.data.vertices):
    raise RuntimeError(f"neutral cage topology mismatch: {len(mesh.vertices)} != {len(body.data.vertices)}")
neutral_cage = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
evaluated.to_mesh_clear()
for modifier in temporarily_hidden:
    modifier.show_viewport = True
bpy.context.view_layer.update()

key = body.shape_key_add(name="ShoulderRaiseTorsoTwist.R", from_mix=False)
key.relative_key = body.data.shape_keys.key_blocks["Basis"]
changed = 0
maximum_delta = 0.0
for vertex in body.data.vertices:
    try:
        if visible.weight(vertex.index) <= 0.0:
            continue
    except RuntimeError:
        continue
    point = neutral_cage[vertex.index]
    lateral = -point.x
    if not (0.078 <= lateral <= 0.265 and -0.155 <= point.y <= 0.115 and 1.025 <= point.z <= 1.345):
        continue
    edge = min(
        (lateral - 0.078) / 0.060,
        (0.265 - lateral) / 0.060,
        (point.y + 0.155) / 0.075,
        (0.115 - point.y) / 0.075,
        (point.z - 1.025) / 0.085,
        (1.345 - point.z) / 0.085,
    )
    weight = smoothstep(edge)
    if weight <= 0.0:
        continue
    delta_lateral = -LATERAL_COMPRESSION * (lateral - 0.1465) * weight
    delta_vertical = -VERTICAL_COMPRESSION * (point.z - 1.170) * weight
    key.data[vertex.index].co.x -= delta_lateral
    key.data[vertex.index].co.z += delta_vertical
    changed += 1
    maximum_delta = max(maximum_delta, (delta_lateral * delta_lateral + delta_vertical * delta_vertical) ** 0.5)

curve = key.driver_add("value")
driver = curve.driver
driver.type = "SCRIPTED"
arm = driver.variables.new()
arm.name = "arm"
arm.type = "SINGLE_PROP"
arm.targets[0].id_type = "OBJECT"
arm.targets[0].id = rig
arm.targets[0].data_path = 'pose.bones["upper_arm.R"].rotation_quaternion[3]'
twist = driver.variables.new()
twist.name = "twist"
twist.type = "SINGLE_PROP"
twist.targets[0].id_type = "OBJECT"
twist.targets[0].id = rig
twist.targets[0].data_path = 'pose.bones["spine_02"].rotation_quaternion[3]'
driver.expression = "max(0,min(1,(arm-0.03)/0.268))*max(0,min(1,((-twist)-0.01)/0.095))"

body["aevrynd_revision"] = f"v249{REVISION}"
body["aevrynd_twist_raise_corrective"] = "right shoulder arm-raise by negative torso-twist interaction shape key"
scene["aevrynd_mainline_revision"] = f"v249{REVISION}-cc0-twist-raise-interaction"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "EXPANDED_DEFORMATION_AND_COLLISION_AUDIT_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "revision": REVISION,
    "lateralCompression": LATERAL_COMPRESSION,
    "verticalCompression": VERTICAL_COMPRESSION,
    "changedVertices": changed,
    "maximumBasisDeltaM": maximum_delta,
    "driver": driver.expression,
    "shapeKeys": len(body.data.shape_keys.key_blocks),
    "status": "EXPANDED_DEFORMATION_AND_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_TWIST_RAISE_INTERACTION=" + json.dumps(report, sort_keys=True))
