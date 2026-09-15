import json
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-shoulder-corrective-shapekeys-r616.blend"
REVISION = os.environ.get("AEVRYND_HIGH_CORRECTIVE_REVISION", "r620")
COMPRESSION = float(os.environ.get("AEVRYND_HIGH_CORRECTIVE_COMPRESSION", "0.70"))
VERTICAL_COMPRESSION = float(os.environ.get("AEVRYND_HIGH_CORRECTIVE_VERTICAL", "0.50"))
OUTPUT = ASSETS / f"aevrynd-female-cc0-high-raise-correctives-{REVISION}.blend"
REPORT = ASSETS / f"female-v249-mainline-cc0-high-raise-correctives-{REVISION}.build.json"
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
    driver.expression = f"max(0,min(1,(({direction})-0.299)/0.070))"
    return driver.expression


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
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

created = {}
for side, sign in (("L", 1.0), ("R", -1.0)):
    key = body.shape_key_add(name=f"ShoulderRaiseHigh.{side}", from_mix=False)
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
        delta_lateral = -COMPRESSION * (lateral - center) * weight
        key.data[vertex.index].co.x += sign * delta_lateral
        delta_vertical = -VERTICAL_COMPRESSION * (point.z - 1.170) * weight
        key.data[vertex.index].co.z += delta_vertical
        changed += 1
        maximum_delta = max(maximum_delta, (delta_lateral * delta_lateral + delta_vertical * delta_vertical) ** 0.5)
    created[side] = {
        "vertices": changed,
        "maximumBasisDeltaM": maximum_delta,
        "driver": add_driver(key, side),
    }

body["aevrynd_revision"] = f"v249{REVISION}"
body["aevrynd_high_raise_corrective"] = "bilateral upper-arm quaternion high-range shape keys"
scene["aevrynd_mainline_revision"] = f"v249{REVISION}-cc0-high-raise-correctives"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "EXPANDED_DEFORMATION_AND_COLLISION_AUDIT_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "revision": REVISION,
    "compression": COMPRESSION,
    "verticalCompression": VERTICAL_COMPRESSION,
    "created": created,
    "shapeKeys": len(body.data.shape_keys.key_blocks),
    "status": "EXPANDED_DEFORMATION_AND_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_HIGH_RAISE_CORRECTIVES=" + json.dumps(report, sort_keys=True))
