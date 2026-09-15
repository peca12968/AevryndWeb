import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-active-shape-rig-r647.blend"
REVISION = os.environ.get("AEVRYND_ELBOW_VOLUME_REVISION", "r655")
EXPANSION = float(os.environ.get("AEVRYND_ELBOW_VOLUME_EXPANSION", "0.35"))
SIGMA = float(os.environ.get("AEVRYND_ELBOW_VOLUME_SIGMA", "0.025"))
OUTPUT = ASSETS / f"aevrynd-female-cc0-elbow-crease-volume-{REVISION}.blend"
REPORT = ASSETS / f"female-v249-mainline-cc0-elbow-crease-volume-{REVISION}.build.json"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"


def add_driver(key, side):
    curve = key.driver_add("value")
    driver = curve.driver
    driver.type = "SCRIPTED"
    variable = driver.variables.new()
    variable.name = "q"
    variable.type = "SINGLE_PROP"
    variable.targets[0].id_type = "OBJECT"
    variable.targets[0].id = bpy.data.objects[RIG]
    variable.targets[0].data_path = f'pose.bones["forearm.{side}"].rotation_quaternion[3]'
    direction = "-q" if side == "L" else "q"
    driver.expression = f"max(0,min(1,(({direction})-0.03)/0.544))"
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
    center = Vector((sign * 0.323902, -0.025325, 1.080822))
    key = body.shape_key_add(name=f"ElbowCreaseVolume70.{side}", from_mix=False)
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
        if delta.length > SIGMA * 3.0:
            continue
        weight = math.exp(-delta.length_squared / (2.0 * SIGMA * SIGMA))
        basis_delta = delta * (EXPANSION * weight)
        key.data[index].co = basis.data[index].co + basis_delta
        changed += 1
        maximum_delta = max(maximum_delta, basis_delta.length)
    created[side] = {
        "vertices": changed,
        "maximumBasisDeltaM": maximum_delta,
        "driver": add_driver(key, side),
    }

body["aevrynd_revision"] = f"v249{REVISION}"
body["aevrynd_elbow_crease_volume"] = "bilateral Gaussian crease-volume expansion driven by elbow flexion"
scene["aevrynd_mainline_revision"] = f"v249{REVISION}-cc0-elbow-crease-volume"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "FULL_JOINT_DEFORMATION_AND_COLLISION_AUDIT_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "revision": REVISION,
    "expansion": EXPANSION, "sigmaM": SIGMA, "created": created,
    "shapeKeys": len(body.data.shape_keys.key_blocks),
    "status": "FULL_JOINT_DEFORMATION_AND_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_ELBOW_CREASE_VOLUME=" + json.dumps(report, sort_keys=True))
